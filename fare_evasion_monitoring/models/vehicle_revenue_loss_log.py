# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
import datetime

_logger = logging.getLogger(__name__)

class VehicleRevenueLossLog(models.Model):
    _name = 'vehicle.revenue.loss.log'
    _description = 'Vehicle Daily Revenue Loss Log'
    _order = 'date desc, name desc'

    name = fields.Char(
        string='Log Reference',
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: _('New')
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle',
        required=True,
        index=True,
        ondelete='restrict' # Prevent deleting vehicle if logs exist
    )
    date = fields.Date(
        string='Date',
        required=True,
        index=True,
        default=fields.Date.context_today
    )
    total_uncarded_passenger_intervals = fields.Float(
        string='Total Uncarded Passenger Intervals',
        readonly=True,
        help="Sum of uncarded passenger instances (after accuracy adjustment) from all 20s logs for the day."
    )
    average_carded_journey_duration_intervals_used = fields.Float(
        string='Avg. Carded Journey Duration (Intervals)',
        readonly=True,
        help="Average journey duration of carded passengers (in 20s intervals) used for this day's estimation."
    )
    estimated_uncarded_journeys = fields.Float(
        string='Est. Uncarded Journeys',
        readonly=True,
        help="Estimated number of unique uncarded passenger journeys for the day. "
             "Calculated as total_uncarded_passenger_intervals / average_carded_journey_duration_intervals_used."
    )
    average_fare_per_carded_trip_used = fields.Monetary(
        string='Avg. Fare per Carded Trip Used',
        readonly=True,
        currency_field='currency_id',
        help="The average fare of a carded trip (from transport.trip data) used for this day's loss estimation."
    )
    total_estimated_lost_revenue = fields.Monetary(
        string='Total Est. Lost Revenue',
        readonly=True,
        currency_field='currency_id',
        help="Total estimated revenue lost on this vehicle for this date. "
             "Calculated as estimated_uncarded_journeys * average_fare_per_carded_trip_used."
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        readonly=True,
        default=lambda self: self.env.company.currency_id.id
    )
    total_20s_logs_processed = fields.Integer(
        string='Total 20s Logs Processed',
        readonly=True,
        help="Number of bus.log records processed for this vehicle and date."
    )
    total_machine_vision_passengers_raw = fields.Integer(
        string='Total MV Passengers (Raw)',
        readonly=True,
        help="Sum of raw machine_vision_count from processed bus.log records."
    )
    total_machine_vision_passengers_adjusted = fields.Float(
        string='Total MV Passengers (Adjusted)',
        readonly=True,
        help="Sum of machine_vision_count after applying the vision_accuracy_factor, from processed bus.log records."
    )
    total_carded_passengers_from_logs = fields.Integer(
        string='Total Carded Passengers (Logs)',
        readonly=True,
        help="Sum of carded_passengers_count from processed bus.log records."
    )
    computation_datetime = fields.Datetime(
        string='Computation Timestamp',
        readonly=True,
        default=fields.Datetime.now
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        default=lambda self: self.env.company
    )
    status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('partial_error', 'Partial Error (e.g., used defaults)'),
        ('no_data', 'No Bus Logs Found'),
        ('error', 'Error During Computation')
        ], string='Status',
        readonly=True,
        default='pending',
        copy=False,
        index=True
    )
    error_message = fields.Text(
        string="Error Details",
        readonly=True,
        copy=False
    )

    _sql_constraints = [
        ('vehicle_date_company_uniq', 'unique(vehicle_id, date, company_id)',
         'A revenue loss log already exists for this vehicle on this date for this company.')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                sequence_date = fields.Date.to_date(vals.get('date')) if vals.get('date') else None
                # Format: VRL/YYYY/MM/SEQ
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'vehicle.revenue.loss.log.sequence', sequence_date=sequence_date
                ) or _('New')
        return super().create(vals_list)

    def _cron_generate_daily_revenue_loss_logs(self, process_date_str=None):
        """
        Generates daily revenue loss logs for each vehicle.
        Implements Algorithm 4.4 from the design document.
        This cron job is intended to run daily to process the previous day's data.

        :param process_date_str: Optional string representation of the date to process (YYYY-MM-DD).
                                 If None, it processes data for 'yesterday'.
        """
        _logger.info("Fare Evasion: Cron job 'Generate Daily Revenue Loss Logs' started.")

        # 1. Determine Processing Date
        if process_date_str:
            try:
                process_date = fields.Date.from_string(process_date_str)
            except ValueError:
                _logger.error(f"Fare Evasion: Invalid date string format '{process_date_str}'. Expected YYYY-MM-DD. Aborting.")
                return
        else:
            process_date = fields.Date.today() - datetime.timedelta(days=1)

        _logger.info(f"Fare Evasion: Processing data for date: {process_date.strftime('%Y-%m-%d')}")

        # Convert process_date to datetime objects for start and end of the day
        day_start_dt = datetime.datetime.combine(process_date, datetime.time.min)
        day_end_dt = datetime.datetime.combine(process_date, datetime.time.max)

        # 2. Pre-fetch System-Wide Configuration and Data
        #    a. Vision accuracy factor
        vision_accuracy_factor = self.env['fare.evasion.utils']._get_config_param('vision_accuracy_factor', 1.0, param_type='float')
        if vision_accuracy_factor <= 0: # As per doc: "If vision_accuracy_factor is None, 0, or an invalid value... use a fallback of 1.0"
            _logger.warning(f"Fare Evasion: Invalid vision_accuracy_factor ({vision_accuracy_factor}). Defaulting to 1.0.")
            vision_accuracy_factor = 1.0

        #    e. Fetch system-wide average trip characteristics for the day
        #       (This is done once for all vehicles for efficiency)
        trip_chars_provider = self.env['fare.evasion.utils']
        avg_trip_characteristics = trip_chars_provider._get_average_carded_trip_characteristics(
            day_start_dt, day_end_dt, use_cache=True # vehicle_id=None for system-wide
        )

        avg_fare_trip = avg_trip_characteristics['average_fare_per_trip']
        avg_duration_intervals_trip = avg_trip_characteristics['average_duration_intervals_per_trip']

        log_creation_status_for_trip_chars = 'success'
        if avg_trip_characteristics['error']:
            log_creation_status_for_trip_chars = 'partial_error'
            _logger.warning(
                f"Fare Evasion: Using default or partially erroneous trip characteristics for {process_date}. "
                f"Details: {avg_trip_characteristics.get('message')}"
            )

        if not avg_trip_characteristics.get('trip_count', 0) and log_creation_status_for_trip_chars == 'success':
            # If no trips were found, it's a partial error because defaults for fare/duration were used.
            log_creation_status_for_trip_chars = 'partial_error'
            _logger.warning(f"Fare Evasion: No carded trips found for {process_date} to determine averages. Defaults were used.")


        # Ensure bus.log model exists
        if 'bus.log' not in self.env:
            _logger.error("Fare Evasion: Critical - 'bus.log' model not found. Cannot process daily logs.")
            # Potentially create a system-level error log or notification here
            return

        # 3. Iterate Through Vehicles
        vehicles = self.env['fleet.vehicle'].search([('active', '=', True)]) # Process for all active vehicles
        _logger.info(f"Fare Evasion: Found {len(vehicles)} active vehicles to process.")

        for vehicle_idx, vehicle in enumerate(vehicles):
            _logger.info(f"Fare Evasion: Processing vehicle {vehicle_idx + 1}/{len(vehicles)}: {vehicle.name} (ID: {vehicle.id}) for date {process_date}.")
            log_vals = {
                'vehicle_id': vehicle.id,
                'date': process_date,
                'currency_id': self.env.company.currency_id.id,
                'company_id': vehicle.company_id.id if vehicle.company_id else self.env.company.id,
                'average_fare_per_carded_trip_used': avg_fare_trip,
                'average_carded_journey_duration_intervals_used': avg_duration_intervals_trip,
                'computation_datetime': fields.Datetime.now(),
            }
            current_log_status = log_creation_status_for_trip_chars # Start with status from trip_char retrieval

            try:
                #    a. Idempotency Check: Skip if log already exists
                existing_log = self.search([
                    ('vehicle_id', '=', vehicle.id),
                    ('date', '=', process_date),
                    ('company_id', '=', vehicle.company_id.id if vehicle.company_id else self.env.company.id)
                ], limit=1)
                if existing_log:
                    _logger.info(f"Fare Evasion: Log for vehicle {vehicle.name} on {process_date} already exists (ID: {existing_log.id}). Skipping.")
                    continue

                #    b. Fetch Bus Logs for the vehicle and day
                #       Fields needed: machine_vision_count, carded_passengers_count
                bus_log_domain = [
                    ('vehicle_id', '=', vehicle.id),
                    ('timestamp', '>=', day_start_dt),
                    ('timestamp', '<=', day_end_dt)
                ]
                # Using search_read for performance if only a few fields are needed.
                bus_logs_data = self.env['bus.log'].search_read(
                    bus_log_domain,
                    fields=['machine_vision_count', 'carded_passengers_count'],
                    order='timestamp asc' # Order not strictly necessary for sums, but good practice
                )

                log_vals['total_20s_logs_processed'] = len(bus_logs_data)

                if not bus_logs_data:
                    _logger.warning(f"Fare Evasion: No bus.log data found for vehicle {vehicle.name} on {process_date}.")
                    log_vals['status'] = 'no_data'
                    log_vals['error_message'] = "No bus.log entries found for this vehicle and date."
                    self.create(log_vals)
                    self.env.cr.commit() # Commit this "no_data" log
                    continue

                #    f. Process Logs & Accumulate
                day_total_uncarded_passenger_intervals = 0.0
                day_mv_raw = 0
                day_mv_adjusted = 0.0
                day_carded_logs = 0

                for log_data in bus_logs_data:
                    mv_count_raw = log_data.get('machine_vision_count', 0)
                    carded_count = log_data.get('carded_passengers_count', 0)

                    # Algorithm 4.1: Machine Vision Accuracy Adjustment
                    # Adjusted_MV_Count = Raw_MV_Count / vision_accuracy_factor
                    # Fallback for vision_accuracy_factor (0 or invalid) is 1.0 (handled above)
                    adjusted_mv_count = mv_count_raw / vision_accuracy_factor

                    # Algorithm 4.2: Uncarded Passengers Calculation (per 20s interval)
                    # Uncarded_Passengers_Interval = max(0, Adjusted_MV_Count - carded_passengers_count)
                    uncarded_passengers_interval = max(0, adjusted_mv_count - carded_count)

                    day_total_uncarded_passenger_intervals += uncarded_passengers_interval
                    day_mv_raw += mv_count_raw
                    day_mv_adjusted += adjusted_mv_count
                    day_carded_logs += carded_count

                log_vals.update({
                    'total_uncarded_passenger_intervals': day_total_uncarded_passenger_intervals,
                    'total_machine_vision_passengers_raw': day_mv_raw,
                    'total_machine_vision_passengers_adjusted': day_mv_adjusted,
                    'total_carded_passengers_from_logs': day_carded_logs,
                })

                #    g. Estimate Uncarded Journeys
                estimated_day_uncarded_journeys = 0.0
                if avg_duration_intervals_trip > 0.01: # Avoid division by zero or tiny unstable numbers
                    estimated_day_uncarded_journeys = day_total_uncarded_passenger_intervals / avg_duration_intervals_trip
                else:
                    _logger.warning(
                        f"Fare Evasion: Average carded journey duration is {avg_duration_intervals_trip} (too low/zero) "
                        f"for vehicle {vehicle.name} on {process_date}. Cannot reliably estimate uncarded journeys. Setting to 0."
                    )
                    # This indicates a more significant issue with base data quality or processing.
                    if current_log_status != 'error': # Don't override a more severe existing error
                         current_log_status = 'partial_error'
                    log_vals['error_message'] = (log_vals.get('error_message', "") +
                                                 " Average carded journey duration was zero or too low; uncarded journeys might be underestimated.").strip()


                log_vals['estimated_uncarded_journeys'] = estimated_day_uncarded_journeys

                #    h. Calculate Total Estimated Lost Revenue
                day_total_estimated_lost_revenue = estimated_day_uncarded_journeys * avg_fare_trip
                log_vals['total_estimated_lost_revenue'] = day_total_estimated_lost_revenue

                log_vals['status'] = current_log_status # This could be 'success' or 'partial_error' from trip_chars or duration issue

                #    i. Create Log Record
                _logger.info(f"Fare Evasion: Creating success/partial_error log for vehicle {vehicle.name} on {process_date} with values: {log_vals}")
                self.create(log_vals)
                self.env.cr.commit() # j. Commit per vehicle

            except Exception as e:
                self.env.cr.rollback() # k. Rollback on error for this vehicle
                error_msg = f"Error processing vehicle {vehicle.name} (ID: {vehicle.id}) for date {process_date}: {e}"
                _logger.error(f"Fare Evasion: {error_msg}", exc_info=True)

                # Create an error log record
                error_log_vals = {
                    'vehicle_id': vehicle.id,
                    'date': process_date,
                    'status': 'error',
                    'error_message': error_msg,
                    'currency_id': self.env.company.currency_id.id,
                    'company_id': vehicle.company_id.id if vehicle.company_id else self.env.company.id,
                    'computation_datetime': fields.Datetime.now(),
                    # Populate other fields with 0 or defaults if possible, to maintain structure
                    'average_fare_per_carded_trip_used': avg_fare_trip, # Use the system-wide one if available
                    'average_carded_journey_duration_intervals_used': avg_duration_intervals_trip,
                }
                try:
                    self.create(error_log_vals)
                    self.env.cr.commit() # Commit the error log
                except Exception as e_log:
                    self.env.cr.rollback()
                    _logger.critical(f"Fare Evasion: CRITICAL - Failed to create error log for vehicle {vehicle.name} on {process_date} after another error. Details: {e_log}")

        _logger.info("Fare Evasion: Cron job 'Generate Daily Revenue Loss Logs' finished.")
