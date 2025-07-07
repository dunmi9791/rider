# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime # Ensure datetime is imported if used directly, though timedelta is from datetime module

_logger = logging.getLogger(__name__)

# Global cache for system-wide daily trip metrics
# Structure: {'cache_key': {'data': {}, 'timestamp': datetime.datetime}}
_system_daily_trip_metrics_cache = {}
CACHE_TIMEOUT_SECONDS = 3600  # 1 hour

class FareEvasionUtils(models.AbstractModel):
    _name = 'fare.evasion.utils'
    _description = 'Fare Evasion Monitoring Utility Functions'

    def _get_config_param(self, param_name, default_value=None, param_type='char'):
        """
        Retrieves a system parameter from ir.config_parameter.
        Handles type casting and provides a default value if not found or if type casting fails.
        Logs warnings for missing parameters or type casting errors.
        """
        full_param_name = f'fare_evasion_monitoring.{param_name}'
        value = self.env['ir.config_parameter'].sudo().get_param(full_param_name)

        if value is False or value is None: # get_param returns False if not found
            _logger.warning(
                f"Fare Evasion Config: Parameter '{full_param_name}' not found. "
                f"Using default value: {default_value}"
            )
            return default_value

        if param_type == 'float':
            try:
                return float(value)
            except ValueError:
                _logger.warning(
                    f"Fare Evasion Config: Could not convert parameter '{full_param_name}' "
                    f"value '{value}' to float. Using default: {default_value}"
                )
                return default_value
        elif param_type == 'int':
            try:
                return int(value)
            except ValueError:
                _logger.warning(
                    f"Fare Evasion Config: Could not convert parameter '{full_param_name}' "
                    f"value '{value}' to integer. Using default: {default_value}"
                )
                return default_value
        elif param_type == 'bool':
            return str(value).lower() in ('true', '1', 'yes')
        # Add other types if needed, e.g., 'json'
        return value # Default is string

    def _get_average_carded_trip_characteristics(self, date_from, date_to, vehicle_id=None, use_cache=False):
        """
        Calculates average fare and duration of carded trips based on historical
        data from the 'transport.trip' model.
        Implements Algorithm 4.3 from the design document.

        :param date_from: datetime object for the start of the period.
        :param date_to: datetime object for the end of the period.
        :param vehicle_id: Optional integer, ID of a specific vehicle to filter trips.
        :param use_cache: Boolean, whether to use system-wide caching if vehicle_id is None.
        :return: A dictionary containing:
            'average_fare_per_trip': float,
            'average_time_seconds_per_trip': float,
            'average_duration_intervals_per_trip': float,
            'currency_id': integer, ID of the company currency,
            'trip_count': integer,
            'error': boolean, True if a significant error occurred or defaults were heavily relied upon.
            'message': string, optional message about the result.
        """
        global _system_daily_trip_metrics_cache, CACHE_TIMEOUT_SECONDS
        company_currency = self.env.company.currency_id
        error_occurred = False
        message_log = []

        # 1. Input Parameters: Handled by method signature.
        _logger.debug(
            f"Fare Evasion Utils: Getting average carded trip characteristics for period "
            f"{date_from} to {date_to}, vehicle_id: {vehicle_id}, use_cache: {use_cache}"
        )

        # 2. Caching (System-wide, if vehicle_id is None and use_cache is True)
        cache_key = None
        if vehicle_id is None and use_cache:
            cache_key = f"{date_from.strftime('%Y-%m-%d_%H%M%S')}_{date_to.strftime('%Y-%m-%d_%H%M%S')}_system_trip_chars"
            if cache_key in _system_daily_trip_metrics_cache:
                cached_entry = _system_daily_trip_metrics_cache[cache_key]
                if (datetime.datetime.now() - cached_entry['timestamp']).total_seconds() < CACHE_TIMEOUT_SECONDS:
                    _logger.info(f"Fare Evasion Utils: Returning cached system-wide trip characteristics for key: {cache_key}")
                    return cached_entry['data']
                else:
                    _logger.info(f"Fare Evasion Utils: Cache expired for key: {cache_key}")
                    del _system_daily_trip_metrics_cache[cache_key]

        # 3. Database Query
        domain = [
            ('start_time', '>=', date_from),
            ('start_time', '<=', date_to), # Assuming transport.trip uses start_time
            ('fare_amount', '>', 0),
            ('time_spent_on_board', '>', 0) # Assuming time_spent_on_board is in seconds
        ]
        if vehicle_id:
            domain.append(('vehicle_id', '=', vehicle_id))

        # Ensure 'transport.trip' model exists
        if 'transport.trip' not in self.env:
            _logger.error("Fare Evasion Utils: 'transport.trip' model not found in the system.")
            error_occurred = True
            message_log.append("Critical: 'transport.trip' model not found.")
            # Fallback to defaults
            def_fare = self._get_config_param('default_carded_trip_fare', 2.50, param_type='float')
            def_dur_sec = self._get_config_param('default_carded_trip_duration_seconds', 900, param_type='int')
            return {
                'average_fare_per_trip': def_fare,
                'average_time_seconds_per_trip': def_dur_sec,
                'average_duration_intervals_per_trip': def_dur_sec / 20.0 if def_dur_sec else 0.0,
                'currency_id': company_currency.id,
                'trip_count': 0,
                'error': True,
                'message': ", ".join(message_log)
            }

        trip_aggregates = []
        try:
            # Group by currency_id to handle multi-currency correctly.
            # Fields to read: fare_amount, time_spent_on_board, and implicitly count per group.
            # The design doc mentions 'currency_id' in fields list for read_group, which is correct.
            # It also mentions 'count:sum' which is not standard; read_group provides '__count'.
            trip_aggregates = self.env['transport.trip'].read_group(
                domain,
                fields=['fare_amount:sum', 'time_spent_on_board:sum', 'currency_id'], # currency_id for grouping
                groupby=['currency_id'], # Group by currency to convert to company currency
                lazy=False # Execute immediately
            )
        except Exception as e: # Catching generic Exception, could be more specific (e.g., psycopg2.Error)
            _logger.error(f"Fare Evasion Utils: Database error during read_group on transport.trip: {e}")
            error_occurred = True
            message_log.append(f"Database query failed: {e}")
            trip_aggregates = [] # Ensure it's an empty list on error

        # 4. Error Handling & Data Aggregation
        total_fare_company_currency = 0.0
        total_time_seconds_all_trips = 0.0
        total_trip_count = 0

        if not trip_aggregates and not error_occurred: # No data found, not necessarily a query error
            _logger.warning(
                f"Fare Evasion Utils: No transport.trip data found for period {date_from} to {date_to} "
                f"with vehicle_id {vehicle_id} and positive fare/duration."
            )
            message_log.append("No valid trip data found for the period.")
            # error_occurred will be True later if defaults are used exclusively.

        for group in trip_aggregates:
            fare_sum = group.get('fare_amount', 0)
            time_sum = group.get('time_spent_on_board', 0)
            count = group.get('__count', 0) # __count is the correct field for group count

            if not count: continue # Should not happen if read_group returns a group

            # currency_id from read_group is a tuple (id, name)
            group_currency_id_tuple = group.get('currency_id')
            if not group_currency_id_tuple:
                _logger.warning(f"Fare Evasion Utils: Skipping group due to missing currency_id. Data: {group}")
                message_log.append("Skipped a trip group due to missing currency information.")
                continue

            current_currency_id = group_currency_id_tuple[0]
            current_currency = self.env['res.currency'].browse(current_currency_id)

            fare_in_company_currency = fare_sum
            if current_currency != company_currency:
                try:
                    # Convert fare_sum to the company's primary currency
                    # The date for conversion should ideally be the date of the transaction,
                    # but date_to (end of the period) is a reasonable approximation here.
                    fare_in_company_currency = current_currency._convert(
                        fare_sum, company_currency, self.env.company, date_to.date()
                    )
                except Exception as e:
                    _logger.error(
                        f"Fare Evasion Utils: Currency conversion failed for amount {fare_sum} "
                        f"from currency {current_currency.name} to {company_currency.name}. Error: {e}"
                    )
                    message_log.append(f"Currency conversion error for {current_currency.name}.")
                    # Decide handling: skip this group's fare or use unconverted if same currency?
                    # For now, we use the original fare_sum if conversion fails and it's already company_currency,
                    # otherwise, this group's fare might be misrepresented or effectively skipped for total.
                    # The current logic adds fare_in_company_currency which defaults to fare_sum.
                    # If it was critical, we might set error_occurred = True here.

            total_fare_company_currency += fare_in_company_currency
            total_time_seconds_all_trips += time_sum
            total_trip_count += count

        # 5. Calculate Averages (with Fallbacks for Fault Tolerance)
        avg_fare_trip = 0.0
        avg_time_seconds_trip = 0.0

        if total_trip_count > 0:
            avg_fare_trip = total_fare_company_currency / total_trip_count
            avg_time_seconds_trip = total_time_seconds_all_trips / total_trip_count
            message_log.append(f"Calculated averages from {total_trip_count} trips.")
        else:
            _logger.warning("Fare Evasion Utils: Zero valid trips found to calculate averages. Using default values.")
            message_log.append("Using default fare and duration as no trips were found.")
            error_occurred = True # Using defaults exclusively is considered a partial error state for the log.

            avg_fare_trip = float(self._get_config_param('default_carded_trip_fare', 2.50, param_type='float'))
            avg_time_seconds_trip = int(self._get_config_param('default_carded_trip_duration_seconds', 900, param_type='int'))
            # Ensure these defaults are logged if used
            message_log.append(f"Default fare: {avg_fare_trip}, Default duration: {avg_time_seconds_trip}s.")


        avg_duration_intervals_trip = avg_time_seconds_trip / 20.0 if avg_time_seconds_trip else 0.0

        result = {
            'average_fare_per_trip': avg_fare_trip,
            'average_time_seconds_per_trip': avg_time_seconds_trip,
            'average_duration_intervals_per_trip': avg_duration_intervals_trip,
            'currency_id': company_currency.id,
            'trip_count': total_trip_count,
            'error': error_occurred, # True if any significant issue or only defaults used.
            'message': ", ".join(message_log)
        }

        # 6. Cache Update (System-wide)
        if vehicle_id is None and use_cache and cache_key and not error_occurred: # Only cache successful, non-error results
            _system_daily_trip_metrics_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.datetime.now()
            }
            _logger.info(f"Fare Evasion Utils: Stored system-wide trip characteristics in cache for key: {cache_key}")
        elif error_occurred and cache_key:
             _logger.warning(f"Fare Evasion Utils: Not caching result for key {cache_key} due to error/defaults.")


        _logger.info(f"Fare Evasion Utils: Average carded trip characteristics result: {result}")
        return result

    def _send_spike_notification(self, vehicle, current_avg_uncarded, historical_avg_uncarded, current_hourly_loss, currency_symbol):
        """
        Sends notifications about fare evasion spikes via Odoo Chatter and Activities.
        Implements the notification logic from Section 7 of the design document.

        :param vehicle: fleet.vehicle record object for the affected vehicle.
        :param current_avg_uncarded: float, current average uncarded passengers in detection window.
        :param historical_avg_uncarded: float, historical average uncarded passengers in comparison window.
        :param current_hourly_loss: float, estimated current hourly loss rate for the vehicle.
        :param currency_symbol: string, currency symbol for the loss amount.
        """
        _logger.info(f"Fare Evasion Utils: Sending spike notification for vehicle {vehicle.name} (ID: {vehicle.id})")

        # 1. Retrieve alert_notification_group_id
        alert_group_id_str = self._get_config_param('alert_notification_group_id', param_type='char') # Stored as char like 'base.group_user' or ID
        alert_group = None

        if alert_group_id_str:
            try:
                # Check if it's an integer ID first
                alert_group_id = int(alert_group_id_str)
                alert_group = self.env['res.groups'].browse(alert_group_id)
                if not alert_group.exists(): # Check if browse returned a valid record
                    alert_group = None # Reset if ID is invalid
                    _logger.warning(f"Fare Evasion Utils: Configured alert_notification_group_id (ID: {alert_group_id_str}) does not exist.")
            except ValueError:
                # If not an int, try to find by full XML ID (e.g., module.group_xml_id)
                try:
                    alert_group = self.env.ref(alert_group_id_str, raise_if_not_found=False)
                except Exception as e: # Broad exception for ref issues
                    _logger.error(f"Fare Evasion Utils: Error trying to find alert group by ref '{alert_group_id_str}': {e}")
                    alert_group = None

            if not alert_group:
                 _logger.warning(
                    f"Fare Evasion Utils: alert_notification_group_id '{alert_group_id_str}' not found or invalid. "
                    "Spike notifications will not be sent to a specific group, only posted on vehicle chatter if applicable."
                )
        else:
            _logger.warning("Fare Evasion Utils: No alert_notification_group_id configured. Notifications might be limited.")

        # 2. Construct HTML formatted message
        message_subject = _("Fare Evasion Spike Alert: %s") % vehicle.name
        message_body_html = _("""
            <p><strong>Fare Evasion Spike Detected!</strong></p>
            <ul>
                <li><strong>Vehicle:</strong> {vehicle_name} (ID: {vehicle_id})</li>
                <li><strong>Detection Time:</strong> {detection_time}</li>
                <li><strong>Current Avg. Uncarded Passengers (Detection Window):</strong> {current_avg:.2f}</li>
                <li><strong>Historical Avg. Uncarded Passengers (Comparison Window):</strong> {historical_avg:.2f}</li>
                <li><strong>Estimated Current Hourly Loss Rate:</strong> {currency_symbol}{hourly_loss:.2f}</li>
            </ul>
            <p>Please investigate this anomaly.</p>
        """).format(
            vehicle_name=vehicle.name or 'N/A',
            vehicle_id=vehicle.id,
            detection_time=fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z'),
            current_avg=current_avg_uncarded,
            historical_avg=historical_avg_uncarded,
            currency_symbol=currency_symbol or '',
            hourly_loss=current_hourly_loss
        )

        # 3. Odoo Chatter Notification on the vehicle
        partner_ids_to_notify = []
        if alert_group and alert_group.users:
            partner_ids_to_notify = alert_group.users.mapped('partner_id.id')
            # Filter out partners that don't exist (e.g., user without partner)
            partner_ids_to_notify = [pid for pid in partner_ids_to_notify if pid]


        try:
            vehicle.message_post(
                body=message_body_html,
                subject=message_subject,
                partner_ids=partner_ids_to_notify, # Notify partners of users in the group
                message_type='notification', # Creates a system notification for recipients
                subtype_xmlid='mail.mt_comment', # Standard comment subtype, can be customized
                author_id=self.env.user.partner_id.id if self.env.user.partner_id else None # Optional: post as current user or system
            )
            _logger.info(f"Fare Evasion Utils: Posted chatter notification on vehicle {vehicle.name}.")
        except Exception as e:
            _logger.error(f"Fare Evasion Utils: Failed to post chatter message on vehicle {vehicle.name}: {e}")

        # 4. Odoo Activity Creation for users in the group
        if alert_group and alert_group.users:
            activity_type_todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            if not activity_type_todo:
                _logger.error("Fare Evasion Utils: Standard 'To Do' activity type (mail.mail_activity_data_todo) not found. Cannot create activities.")
                return # Cannot proceed with activity creation

            activity_model_id = self.env['ir.model']._get('fleet.vehicle').id

            for user in alert_group.users:
                if not user.partner_id: # User must have a partner to be assigned activities this way
                    _logger.warning(f"Fare Evasion Utils: User {user.login} in alert group has no linked partner. Skipping activity creation for this user.")
                    continue

                activity_vals = {
                    'activity_type_id': activity_type_todo.id,
                    'summary': _("Investigate Fare Evasion Spike: %s") % vehicle.name,
                    'note': message_body_html, # Use the same HTML message for context
                    'user_id': user.id,
                    'res_id': vehicle.id,
                    'res_model_id': activity_model_id,
                    'date_deadline': fields.Date.today() # Due today
                }
                try:
                    self.env['mail.activity'].create(activity_vals)
                    _logger.info(f"Fare Evasion Utils: Created 'To Do' activity for user {user.login} regarding spike on vehicle {vehicle.name}.")
                except Exception as e:
                    _logger.error(f"Fare Evasion Utils: Failed to create activity for user {user.login} for vehicle {vehicle.name}: {e}")
        elif not alert_group:
             _logger.info("Fare Evasion Utils: No alert group specified or found, so no user-specific activities created.")
        elif not alert_group.users:
             _logger.info(f"Fare Evasion Utils: Alert group '{alert_group.name}' has no users. No activities created.")


    def _clear_system_trip_metrics_cache(self, key_prefix=None):
        """
        Clears the system trip metrics cache.
        If key_prefix is provided, only keys starting with that prefix are cleared.
        Otherwise, the entire cache is cleared.
        """
        global _system_daily_trip_metrics_cache
        if key_prefix:
            keys_to_delete = [k for k in _system_daily_trip_metrics_cache if k.startswith(key_prefix)]
            for k in keys_to_delete:
                del _system_daily_trip_metrics_cache[k]
            _logger.info(f"Fare Evasion Cache: Cleared entries with prefix '{key_prefix}'.")
        else:
            _system_daily_trip_metrics_cache.clear()
            _logger.info("Fare Evasion Cache: Cleared all system trip metrics cache.")

    # Example of how vision accuracy factor might be fetched if it's more complex
    # than a direct _get_config_param call in the main logic.
    # For now, direct call in algorithm is fine as per design.
    # def _get_vision_accuracy_factor(self, vehicle=None):
    #     """
    #     Retrieves the vision accuracy factor.
    #     Placeholder for potential future enhancement allowing per-vehicle accuracy.
    #     Currently returns system-wide configured value.
    #     """
    #     return self._get_config_param('vision_accuracy_factor', 1.0, param_type='float')

# Ensure the global cache variable is defined at the module level
# _system_daily_trip_metrics_cache = {}
# CACHE_TIMEOUT_SECONDS = 3600 # 1 hour (already defined above)
