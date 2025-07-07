# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
import datetime

_logger = logging.getLogger(__name__)

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    last_revenue_spike_alert_time = fields.Datetime(
        string='Last Revenue Spike Alert Time',
        readonly=True,
        copy=False,
        help="Timestamp of the last fare evasion spike alert sent for this vehicle."
    )
    current_estimated_hourly_loss = fields.Monetary(
        string='Current Est. Hourly Loss (Near Real-Time)',
        currency_field='company_currency_id', # Assuming fleet.vehicle has company_currency_id or similar
                                              # If not, need to add currency_id or relate to company_id.currency_id
        readonly=True,
        copy=False,
        help="Near real-time estimated revenue loss per hour for this vehicle, updated by the spike detection cron."
    )
    # Helper field to get company currency, common in Odoo models
    # If fleet.vehicle already has a company_id and through it currency_id, this might not be strictly needed
    # but explicit is often better.
    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        string="Company Currency",
        readonly=True,
        store=True # Store for easier access in views/reports if needed
    )
    last_hourly_loss_update_time = fields.Datetime(
        string='Last Hourly Loss Update Time',
        readonly=True,
        copy=False,
        help="Timestamp when the 'Current Est. Hourly Loss' was last calculated."
    )

    # If company_id is not standard on fleet.vehicle, we might need to add it or ensure it's available.
    # Most Odoo models linked to company data have it. Let's assume it exists.
    # If not, it would be:
    # company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def _cron_check_revenue_loss_spikes(self):
        """
        Periodically analyzes recent bus.log data to identify and alert on fare evasion spikes,
        and updates near real-time metrics on the vehicle.
        Implements Algorithm 4.5 from the design document.
        """
        _logger.info("Fare Evasion: Cron job 'Check Revenue Loss Spikes & Update Metrics' started.")
        fem_utils = self.env['fare.evasion.utils']

        # 1. Initialization
        #    b. Fetch all relevant configuration parameters
        config_params = {
            'accuracy': fem_utils._get_config_param('vision_accuracy_factor', 1.0, param_type='float'),
            'detection_window_minutes': fem_utils._get_config_param('spike_detection_window_minutes', 15, param_type='int'),
            'comparison_window_hours': fem_utils._get_config_param('spike_comparison_window_hours', 2, param_type='int'),
            'threshold_percentage': fem_utils._get_config_param('spike_threshold_percentage', 50.0, param_type='float'),
            'min_uncarded_alert': fem_utils._get_config_param('min_uncarded_for_spike_alert', 5, param_type='int'),
            'cool_down_minutes': fem_utils._get_config_param('last_spike_alert_cool_down_minutes', 60, param_type='int'),
            'min_logs_eval': fem_utils._get_config_param('min_logs_for_spike_eval', 3, param_type='int'),
        }
        # Validate vision accuracy factor
        if config_params['accuracy'] <= 0:
            _logger.warning(f"Fare Evasion Spike Check: Invalid vision_accuracy_factor ({config_params['accuracy']}). Defaulting to 1.0.")
            config_params['accuracy'] = 1.0

        #    c. now_dt
        now_dt = fields.Datetime.now()

        #    d. Define time windows
        detection_start_dt = now_dt - datetime.timedelta(minutes=config_params['detection_window_minutes'])
        comparison_end_dt = detection_start_dt # Historical window ends where current detection window begins
        comparison_start_dt = comparison_end_dt - datetime.timedelta(hours=config_params['comparison_window_hours'])

        #    e. Get recent system-wide trip characteristics for loss estimation (e.g., last 24 hours)
        #       Using a fixed recent period (e.g., 24h) for trip chars to avoid too much volatility from very short term data.
        recent_trip_chars_start_dt = now_dt - datetime.timedelta(hours=24)
        recent_trip_chars = fem_utils._get_average_carded_trip_characteristics(
            recent_trip_chars_start_dt, now_dt, use_cache=True
        )

        if recent_trip_chars['error'] or recent_trip_chars['trip_count'] == 0:
            _logger.critical(
                "Fare Evasion Spike Check: Cannot proceed with spike monetary loss estimation. "
                f"Failed to get valid recent average trip characteristics. Error: {recent_trip_chars.get('message')}"
            )
            # Gracefully exit cron; daily log will capture more detailed errors if any.
            # This cron focuses on spikes, if it can't estimate loss, it can still detect occurrence.
            # However, the design doc says "return True (gracefully exit cron)" if this fails.
            # For now, we will allow spike detection to proceed but loss estimation will be zero.
            # An alternative is to fetch default fare from config if trip_chars fail.
            default_fare_if_error = fem_utils._get_config_param('default_carded_trip_fare', 2.5, param_type='float')
            default_duration_if_error = fem_utils._get_config_param('default_carded_trip_duration_seconds', 900, param_type='int') / 20.0

            recent_avg_fare_trip = default_fare_if_error
            recent_avg_duration_intervals_trip = default_duration_if_error
            company_currency_id = self.env.company.currency_id.id
            currency_symbol = self.env.company.currency_id.symbol
            _logger.warning(f"Fare Evasion Spike Check: Using default fare ({recent_avg_fare_trip}) and duration ({recent_avg_duration_intervals_trip} intervals) due to error in trip_chars.")

        else:
            recent_avg_fare_trip = recent_trip_chars['average_fare_per_trip']
            recent_avg_duration_intervals_trip = recent_trip_chars['average_duration_intervals_per_trip']
            company_currency_id = recent_trip_chars['currency_id']
            currency_symbol = self.env['res.currency'].browse(company_currency_id).symbol


        if 'bus.log' not in self.env:
            _logger.error("Fare Evasion Spike Check: Critical - 'bus.log' model not found. Aborting spike check.")
            return

        # 2. Iterate Vehicles
        vehicles = self.env['fleet.vehicle'].search([('active', '=', True)])
        _logger.info(f"Fare Evasion Spike Check: Processing {len(vehicles)} active vehicles.")

        for vehicle_idx, vehicle in enumerate(vehicles):
            _logger.debug(f"Fare Evasion Spike Check: Vehicle {vehicle_idx+1}/{len(vehicles)}: {vehicle.name} (ID: {vehicle.id})")
            current_vehicle_hourly_loss = 0.0 # Initialize for each vehicle

            try:
                # b. Alert Cool-down Check
                if vehicle.last_revenue_spike_alert_time and \
                   (now_dt - vehicle.last_revenue_spike_alert_time).total_seconds() < config_params['cool_down_minutes'] * 60:
                    _logger.info(f"Fare Evasion Spike Check: Alert cool-down active for vehicle {vehicle.name}. Skipping alert check.")
                    # Still update hourly loss if possible
                    # Fetch data and calculate current_avg_uncarded for hourly loss update (steps c-e, i)

                # c. Fetch Current Window Data
                current_logs_data = self.env['bus.log'].search_read(
                    [('vehicle_id', '=', vehicle.id), ('timestamp', '>=', detection_start_dt), ('timestamp', '<', now_dt)],
                    fields=['machine_vision_count', 'carded_passengers_count']
                )

                # d. Minimum Logs Check for current window
                if len(current_logs_data) < config_params['min_logs_eval']:
                    _logger.info(
                        f"Fare Evasion Spike Check: Insufficient current log data ({len(current_logs_data)} found, "
                        f"{config_params['min_logs_eval']} required) for vehicle {vehicle.name}. Skipping spike analysis."
                    )
                    # Update hourly loss to 0 or based on available data if desired, or leave as is.
                    # Design doc implies 'continue', so we won't update hourly loss if insufficient data for spike eval.
                    # However, it's better to set it to 0 if we can't evaluate.
                    vehicle.sudo().write({
                        'current_estimated_hourly_loss': 0.0,
                        'last_hourly_loss_update_time': now_dt
                    })
                    self.env.cr.commit()
                    continue

                # e. Calculate current_avg_uncarded
                current_total_uncarded_intervals = 0.0
                for log_entry in current_logs_data:
                    mv_raw = log_entry.get('machine_vision_count', 0)
                    carded = log_entry.get('carded_passengers_count', 0)
                    adj_mv = mv_raw / config_params['accuracy'] if config_params['accuracy'] > 0 else mv_raw
                    uncarded_interval = max(0, adj_mv - carded)
                    current_total_uncarded_intervals += uncarded_interval
                current_avg_uncarded = current_total_uncarded_intervals / len(current_logs_data)

                # i. Calculate Current Estimated Hourly Loss (Done here as current_avg_uncarded is available)
                #    This part of Algorithm 4.5 step 2.i
                estimated_uncarded_journeys_per_interval_in_window = 0.0
                if recent_avg_duration_intervals_trip > 0.01:
                    estimated_uncarded_journeys_per_interval_in_window = current_avg_uncarded / recent_avg_duration_intervals_trip
                else: # Fallback if average trip duration is unknown
                    # As per doc: "assumes each uncarded passenger instance is a distinct, short journey"
                    # This effectively means current_avg_uncarded represents journeys per 20s interval if duration is 1 interval.
                    # If we interpret it as current_avg_uncarded *is* the number of short journeys in that interval:
                    estimated_uncarded_journeys_per_interval_in_window = current_avg_uncarded
                    _logger.debug(f"Vehicle {vehicle.name}: Using fallback for uncarded journeys calculation due to low/zero avg trip duration.")

                estimated_loss_rate_per_20s_interval = estimated_uncarded_journeys_per_interval_in_window * recent_avg_fare_trip
                current_vehicle_hourly_loss = estimated_loss_rate_per_20s_interval * 180 # (3600s/hr / 20s/interval = 180 intervals/hr)

                # j. Update Vehicle (Near Real-Time Metric for Dashboard)
                vehicle.sudo().write({
                    'current_estimated_hourly_loss': current_vehicle_hourly_loss,
                    'last_hourly_loss_update_time': now_dt
                })
                # Spike check continues below, commit will happen after spike check or at end of try block.

                # f. Fetch Comparison Window Data
                historical_logs_data = self.env['bus.log'].search_read(
                    [('vehicle_id', '=', vehicle.id), ('timestamp', '>=', comparison_start_dt), ('timestamp', '<', comparison_end_dt)],
                    fields=['machine_vision_count', 'carded_passengers_count']
                )

                # g. Calculate historical_avg_uncarded
                historical_avg_uncarded = 0.0
                if historical_logs_data: # Check if there's any historical data
                    historical_total_uncarded_intervals = 0.0
                    for log_entry in historical_logs_data:
                        mv_raw = log_entry.get('machine_vision_count', 0)
                        carded = log_entry.get('carded_passengers_count', 0)
                        adj_mv = mv_raw / config_params['accuracy'] if config_params['accuracy'] > 0 else mv_raw
                        uncarded_interval = max(0, adj_mv - carded)
                        historical_total_uncarded_intervals += uncarded_interval
                    historical_avg_uncarded = historical_total_uncarded_intervals / len(historical_logs_data)
                else:
                    _logger.info(f"Fare Evasion Spike Check: No historical log data for vehicle {vehicle.name} in comparison window. Baseline is 0.")
                    # historical_avg_uncarded remains 0.0

                # h. Spike Check Logic
                percentage_increase = 0.0
                if historical_avg_uncarded > 0.01: # Avoid division by zero if baseline is effectively zero
                    percentage_increase = ((current_avg_uncarded - historical_avg_uncarded) / historical_avg_uncarded) * 100.0
                elif current_avg_uncarded > 0.01: # Current is positive, baseline was zero
                    percentage_increase = 99999.0 # Effectively infinite increase
                # else: percentage_increase remains 0.0 (both current and historical are zero)

                is_spike = percentage_increase >= config_params['threshold_percentage']
                is_significant = current_avg_uncarded >= config_params['min_uncarded_alert']

                _logger.debug(
                    f"Vehicle {vehicle.name}: Current Avg Uncarded={current_avg_uncarded:.2f}, "
                    f"Historical Avg Uncarded={historical_avg_uncarded:.2f}, "
                    f"Increase={percentage_increase:.2f}%, Spike Threshold={config_params['threshold_percentage']}%, "
                    f"Min Uncarded Alert={config_params['min_uncarded_alert']}. "
                    f"IsSpike={is_spike}, IsSignificant={is_significant}."
                )

                # k. Alerting
                if is_spike and is_significant:
                    # Re-check cool-down before sending alert
                    if vehicle.last_revenue_spike_alert_time and \
                       (now_dt - vehicle.last_revenue_spike_alert_time).total_seconds() < config_params['cool_down_minutes'] * 60:
                        _logger.info(f"Fare Evasion Spike Check: Spike detected for {vehicle.name} but cool-down is active. Alert NOT sent.")
                    else:
                        _logger.warning(
                            f"Fare Evasion Spike ALERT: Vehicle {vehicle.name} triggered a spike. "
                            f"Current Avg Uncarded: {current_avg_uncarded:.2f}, "
                            f"Historical Avg Uncarded: {historical_avg_uncarded:.2f}, "
                            f"Est. Hourly Loss: {currency_symbol}{current_vehicle_hourly_loss:.2f}."
                        )
                        fem_utils._send_spike_notification(
                            vehicle,
                            current_avg_uncarded,
                            historical_avg_uncarded,
                            current_vehicle_hourly_loss,
                            currency_symbol
                        )
                        vehicle.sudo().write({'last_revenue_spike_alert_time': now_dt})

                self.env.cr.commit() # l. Commit changes for this vehicle (hourly loss, last alert time)

            except Exception as e:
                self.env.cr.rollback() # m. Rollback on error for this vehicle
                _logger.error(
                    f"Fare Evasion Spike Check: Error processing vehicle {vehicle.name} (ID: {vehicle.id}): {e}",
                    exc_info=True
                )
                # Do not commit if an error occurred for this vehicle.

        _logger.info("Fare Evasion: Cron job 'Check Revenue Loss Spikes & Update Metrics' finished.")


    def action_view_revenue_loss_logs(self):
        """
        Action to open the revenue loss logs for this vehicle.
        """
        self.ensure_one()
        return {
            'name': _('Revenue Loss Logs for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'vehicle.revenue.loss.log',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id}
        }

    # For dashboard navigation - count of logs
    revenue_loss_log_count = fields.Integer(
        compute='_compute_revenue_loss_log_count',
        string="Revenue Loss Logs Count"
    )

    def _compute_revenue_loss_log_count(self):
        for vehicle in self:
            vehicle.revenue_loss_log_count = self.env['vehicle.revenue.loss.log'].search_count(
                [('vehicle_id', '=', vehicle.id)]
            )
