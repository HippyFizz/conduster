from django.core.management import call_command
from django_cron import CronJobBase, Schedule


class UpdateGeoData(CronJobBase):
    # every month
    schedule = Schedule(run_every_mins=24 * 60 * 31, retry_after_failure_mins=60)
    code = 'collector.UpdateGeoData'    # a unique code

    def do(self):
        call_command('update_geo_data', settings='condust.settings')


class FillLeads(CronJobBase):
    # every 1 minute
    schedule = Schedule(run_every_mins=1, retry_after_failure_mins=1)
    code = 'collector.FillLeads'  # a unique code

    def do(self):
        call_command('fill_leads', settings='condust.settings')


class FillIpStat(CronJobBase):
    # at 1:00 am every day
    schedule = Schedule(run_at_times=['1:00'], retry_after_failure_mins=30)
    code = 'collector.FillIpStat'  # a unique code

    def do(self):
        call_command('fill_ip_stat', settings='condust.settings')
        call_command('clean_ip_stat_csv', settings='condust.settings')
