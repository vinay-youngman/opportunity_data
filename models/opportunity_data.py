from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class OpportunityData(models.TransientModel):
    _name = 'opportunity.data'
    _description = 'Opportunity Data'

    sales_person_id = fields.Char(string='Sales Person Name')
    name = fields.Char(string='Partner Name', required=True)
    total_needs_identified_count = fields.Float(string='Total Needs Identified Count')
    total_expected_revenue_needs_identified = fields.Float(string='Total Expected Revenue (Needs Identified)')
    total_quotation_sent_count = fields.Integer(string='Total Quotation Sent Count')
    total_expected_revenue_quotation_sent = fields.Float(string='Total Expected Revenue (Quotation Sent)')
    total_won_count = fields.Integer(string='Total Won Count')
    total_expected_revenue_won = fields.Float(string='Total Expected Revenue (Won)')
    total_lost_count = fields.Integer(string='Total Lost Count')
    total_expected_revenue_lost = fields.Float(string='Total Expected Revenue (Lost)')
    total_opportunites_created_today = fields.Integer(string='No. of Opportunities Created Today')

    @api.model
    def update_partner_opportunity_stats(self):
        try:
            # Truncate the table first
            query_truncate = """
            TRUNCATE TABLE opportunity_data;
            """
            self.env.cr.execute(query_truncate)
            self.env.cr.commit()

            query = """
           
WITH NeedsIdentification AS (
    SELECT
        res_users.login AS Login,
        COALESCE(res_partner.name, 'No Master Customer') AS Master_customer,
        COUNT(crm_lead.id) AS total_needs_identification_count,
        SUM(crm_lead.expected_revenue) AS total_needs_identification_count_expected_revenue,
        0 AS total_quotation_sent_count,
        0 AS total_quotation_sent_count_expected_revenue
    FROM
        crm_lead
    LEFT JOIN res_partner ON crm_lead.partner_id = res_partner.id
    INNER JOIN res_users ON crm_lead.user_id = res_users.id
    WHERE
        crm_lead.type = 'opportunity'
        AND crm_lead.stage_id = 1
        AND crm_lead.active = true
    GROUP BY
        res_users.login,
        COALESCE(res_partner.name, 'No Master Customer')
),
QuotationSent AS (
    SELECT
        res_users.login AS Login,
        COALESCE(res_partner.name, 'No Master Customer') AS Master_customer,
        0 AS total_needs_identification_count,
        0 AS total_needs_identification_count_expected_revenue,
        COUNT(crm_lead.id) AS total_quotation_sent_count,
        SUM(crm_lead.expected_revenue) AS total_quotation_sent_count_expected_revenue
    FROM
        crm_lead
    LEFT JOIN res_partner ON crm_lead.partner_id = res_partner.id
    INNER JOIN res_users ON crm_lead.user_id = res_users.id
    WHERE
        crm_lead.type = 'opportunity'
        AND crm_lead.stage_id = 2
        AND crm_lead.active = true
    GROUP BY
        res_users.login,
        COALESCE(res_partner.name, 'No Master Customer')
),
TotalOpportunities AS (
    SELECT
        res_users.login AS Login,
        COALESCE(res_partner.name, 'No Master Customer') AS Master_customer,
        COUNT(crm_lead.id) AS total_opportunities
    FROM
        crm_lead
    LEFT JOIN res_partner ON crm_lead.partner_id = res_partner.id
    INNER JOIN res_users ON crm_lead.user_id = res_users.id
    WHERE
        crm_lead.type = 'opportunity'
        AND crm_lead.active = true
        AND (
            (date(crm_lead.create_date) = current_date AND crm_lead.date_conversion IS NULL)
            OR (date(crm_lead.date_conversion) = current_date)
        )
    GROUP BY
        res_users.login,
        COALESCE(res_partner.name, 'No Master Customer')
),
WonLost AS (
    SELECT
        res_users.login AS Login,
        COALESCE(res_partner.name, 'No Master Customer') AS Master_customer,
        COUNT(CASE WHEN crm_lead.stage_id = 4 AND crm_lead.active = true AND date(crm_lead.date_closed) = current_date THEN crm_lead.id ELSE NULL END) AS total_won_count_on_that_day,
        SUM(CASE WHEN crm_lead.stage_id = 4 AND crm_lead.active = true AND date(crm_lead.date_closed) = current_date THEN crm_lead.expected_revenue ELSE 0 END) AS total_won_count_on_that_day_expected_revenue,
        COUNT(CASE WHEN crm_lead.active = false AND date(crm_lead.date_closed) = current_date THEN crm_lead.id ELSE NULL END) AS total_lost_count,
        SUM(CASE WHEN crm_lead.active = false AND date(crm_lead.date_closed) = current_date THEN crm_lead.expected_revenue ELSE 0 END) AS total_lost_count_expected_revenue
    FROM
        crm_lead
    LEFT JOIN res_partner ON crm_lead.partner_id = res_partner.id
    INNER JOIN res_users ON crm_lead.user_id = res_users.id
    WHERE
        crm_lead.type = 'opportunity'
        AND ((crm_lead.stage_id = 4 AND crm_lead.active = true AND date(crm_lead.date_closed) = current_date)
            OR (crm_lead.active = false AND date(crm_lead.date_closed) = current_date)
        )
    GROUP BY
        res_users.login,
        COALESCE(res_partner.name, 'No Master Customer')
),
LostOpportunities AS (
    SELECT
        res_users.login AS Login,
        COALESCE(res_partner.name, 'No Master Customer') AS Master_customer,
        COUNT(crm_lead.id) AS total_lost_count,
        SUM(crm_lead.expected_revenue) AS total_lost_count_expected_revenue
    FROM
        crm_lead
    LEFT JOIN res_partner ON crm_lead.partner_id = res_partner.id
    INNER JOIN res_users ON crm_lead.user_id = res_users.id
    WHERE
        crm_lead.type = 'opportunity'
        AND crm_lead.active = false
        AND date(crm_lead.date_closed) = current_date
    GROUP BY
        res_users.login,
        COALESCE(res_partner.name, 'No Master Customer')
)
SELECT
    COALESCE(NI.Login, QS.Login, TOp.Login, WL.Login, LO.Login) AS Login,
    COALESCE(NI.Master_customer, QS.Master_customer, TOp.Master_customer, WL.Master_customer, LO.Master_customer) AS Master_customer,
    SUM(COALESCE(NI.total_needs_identification_count, 0)) AS total_needs_identification_count,
    SUM(COALESCE(NI.total_needs_identification_count_expected_revenue, 0)) AS total_needs_identification_count_expected_revenue,
    SUM(COALESCE(QS.total_quotation_sent_count, 0)) AS total_quotation_sent_count,
    SUM(COALESCE(QS.total_quotation_sent_count_expected_revenue, 0)) AS total_quotation_sent_count_expected_revenue,
    SUM(COALESCE(TOp.total_opportunities, 0)) AS total_opportunities,
    SUM(COALESCE(WL.total_won_count_on_that_day, 0)) AS total_won_count_on_that_day,
    SUM(COALESCE(WL.total_won_count_on_that_day_expected_revenue, 0)) AS total_won_count_on_that_day_expected_revenue,
    SUM(COALESCE(LO.total_lost_count, 0)) AS total_lost_count,
    SUM(COALESCE(LO.total_lost_count_expected_revenue, 0)) AS total_lost_count_expected_revenue
FROM NeedsIdentification NI
FULL JOIN QuotationSent QS ON NI.Login = QS.Login AND NI.Master_customer = QS.Master_customer
FULL JOIN TotalOpportunities TOp ON TOp.Login = COALESCE(NI.Login, QS.Login) AND TOp.Master_customer = COALESCE(NI.Master_customer, QS.Master_customer)
FULL JOIN WonLost WL ON COALESCE(NI.Login, QS.Login, TOp.Login) = WL.Login AND COALESCE(NI.Master_customer, QS.Master_customer, TOp.Master_customer) = WL.Master_customer
FULL JOIN LostOpportunities LO ON COALESCE(NI.Login, QS.Login, TOp.Login, WL.Login) = LO.Login AND COALESCE(NI.Master_customer, QS.Master_customer, TOp.Master_customer, WL.Master_customer) = LO.Master_customer
GROUP BY
    COALESCE(NI.Login, QS.Login, TOp.Login, WL.Login, LO.Login),
    COALESCE(NI.Master_customer, QS.Master_customer, TOp.Master_customer, WL.Master_customer, LO.Master_customer);
            """
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()

            for row in result:
                vals = {
                    'sales_person_id': row[0],
                    'name': row[1],
                    'total_needs_identified_count': row[2],
                    'total_expected_revenue_needs_identified': row[3],
                    'total_quotation_sent_count': row[4],
                    'total_expected_revenue_quotation_sent': row[5],
                    'total_won_count': row[6],
                    'total_lost_count': row[7],
                    'total_expected_revenue_lost': row[8],
                }
                create_first_data = self.create(vals)
                _logger.info('Created record with ID: %s', create_first_data.id)

            # Commit the transaction
            self.env.cr.commit()
        except Exception as e:
            _logger.error("Error while writing to the database: %s", e)
