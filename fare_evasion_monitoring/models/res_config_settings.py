# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Fare Evasion Monitoring Section Title (for grouping in settings view)
    module_fare_evasion_monitoring = fields.Boolean(
        string="Fare Evasion Monitoring",
        implied_group='fare_evasion_monitoring.group_fare_evasion_user', # A basic user group
        help="Enable to configure fare evasion monitoring parameters."
    )

    group_fare_evasion_manager = fields.Boolean(
        string="Fare Evasion Manager",
        implied_group='fare_evasion_monitoring.group_fare_evasion_manager',
        help="Users in this group can configure advanced settings and receive all alerts."
    )

    # Vision System Accuracy
    vision_accuracy_factor = fields.Float(
        string='Vision System Accuracy Factor (0.0 to 1.0)',
        config_parameter='fare_evasion_monitoring.vision_accuracy_factor',
        default=0.65,
        help="Adjusts raw machine vision counts. E.g., if vision system counts 65% of actual passengers, set to 0.65. "
             "A value of 1.0 means no adjustment."
    )

    # Spike Detection Parameters
    spike_detection_window_minutes = fields.Integer(
        string='Spike Detection Window (Minutes)',
        config_parameter='fare_evasion_monitoring.spike_detection_window_minutes',
        default=15,
        help="Defines the 'current' period (in minutes) for spike analysis."
    )
    spike_comparison_window_hours = fields.Integer(
        string='Spike Comparison Window (Hours)',
        config_parameter='fare_evasion_monitoring.spike_comparison_window_hours',
        default=2,
        help="Defines the 'historical baseline' period (in hours) for spike analysis."
    )
    spike_threshold_percentage = fields.Float(
        string='Spike Threshold Percentage Increase (%)',
        config_parameter='fare_evasion_monitoring.spike_threshold_percentage',
        default=50.0,
        help="The percentage increase of current uncarded average over historical average that triggers a spike alert."
    )
    min_uncarded_for_spike_alert = fields.Integer(
        string='Min. Avg Uncarded Passengers for Spike Alert',
        config_parameter='fare_evasion_monitoring.min_uncarded_for_spike_alert',
        default=5,
        help="Absolute minimum average of uncarded passengers in the detection window to trigger an alert. "
             "Prevents alerts for minor percentage changes when actual numbers are very low."
    )
    alert_notification_group_id = fields.Many2one(
        'res.groups',
        string='Spike Alert Notification Group',
        config_parameter='fare_evasion_monitoring.alert_notification_group_id',
        help="Determines which user group receives Odoo notifications (chatter, activities) for spike alerts."
    )
    last_spike_alert_cool_down_minutes = fields.Integer(
        string='Spike Alert Cool-down (Minutes)',
        config_parameter='fare_evasion_monitoring.last_spike_alert_cool_down_minutes',
        default=60,
        help="Prevents spamming alerts for the same ongoing spike on a vehicle. "
             "A new alert for the same vehicle will only be sent after this period."
    )
    min_logs_for_spike_eval = fields.Integer(
        string='Min. Bus Logs for Spike Evaluation',
        config_parameter='fare_evasion_monitoring.min_logs_for_spike_eval',
        default=3,
        help="Minimum number of bus.log records required within the spike_detection_window_minutes "
             "to proceed with a spike evaluation for a vehicle."
    )

    # Default Fallback Values
    default_carded_trip_duration_seconds = fields.Integer(
        string='Default Carded Trip Duration (seconds)',
        config_parameter='fare_evasion_monitoring.default_carded_trip_duration_seconds',
        default=900, # 15 minutes
        help="Fallback value (in seconds). Used if average duration cannot be calculated from transport.trip data."
    )
    default_carded_trip_fare = fields.Float(
        string='Default Carded Trip Fare',
        config_parameter='fare_evasion_monitoring.default_carded_trip_fare',
        default=2.50,
        help="Fallback value. Used if average fare cannot be calculated from transport.trip data."
    )

    @api.onchange('vision_accuracy_factor')
    def _onchange_vision_accuracy_factor(self):
        if self.vision_accuracy_factor <= 0 or self.vision_accuracy_factor > 1.0:
            # Consider if we want to raise a warning directly in UI or just let the backend handle it.
            # For now, this is a silent check; backend _get_config_param will use default if invalid.
            # A UserError could be raised here for immediate feedback:
            # raise UserError(_("Vision system accuracy factor must be between 0 (exclusive) and 1.0 (inclusive)."))
            pass # Let backend handle invalid values gracefully by using defaults.

    # Add more onchange methods for validation if necessary for other fields.
    # For example, ensuring window_minutes > 0 etc.
    # The _get_config_param in utils will handle type errors and missing params gracefully.

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        # If any parameter needs specific handling upon saving, do it here.
        # For example, clearing a cache if a critical parameter changes.
        # self.env['fare.evasion.utils']._clear_system_trip_metrics_cache() # Example
        # Be cautious with clearing cache on every settings save, only if necessary.

        # Ensure the implied groups are created if they don't exist
        # This is typically handled by Odoo automatically based on the implied_group attribute
        # but can be explicitly managed if needed.
        pass

    # get_values can be overridden if some values need to be computed before display
    # but for config_parameter, Odoo handles this automatically.
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     # res.update(...)
    #     return res
