#   Copyright 2016 Huawei, Inc. All rights reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#
import argparse
import logging

from keystoneauth1 import exceptions
from osc_lib.command import command

from antiddosclient.common import parser as p
from antiddosclient.common import resource as br
from antiddosclient.common import parsetypes
from antiddosclient.common.i18n import _
from antiddosclient.osc.v1 import parser_builder as pb
from antiddosclient.v1 import resource

LOG = logging.getLogger(__name__)


class QueryAntiDDosConfig(command.ShowOne):
    _description = _("Query AntiDDos configurations")

    def get_parser(self, prog_name):
        parser = super(QueryAntiDDosConfig, self).get_parser(prog_name)
        return parser

    def take_action(self, args):
        client = self.app.client_manager.antiddos
        data = client.antiddos.query_config_list()
        columns = resource.AntiDDosConfig.show_column_names
        formatter = resource.AntiDDosConfig.formatter
        return columns, data.get_display_data(columns, formatter=formatter)


class OpenAntiDDos(command.Command):
    _description = _("Open AntiDDos for floating IP")

    def get_parser(self, prog_name):
        parser = super(OpenAntiDDos, self).get_parser(prog_name)
        pb.AntiDDosParser.add_floating_ip_arg(parser)
        pb.AntiDDosParser.add_enable_l7_arg(parser)
        pb.AntiDDosParser.add_maximum_service_traffic_arg(parser)
        pb.AntiDDosParser.add_http_request_rate_arg(parser)
        # pb.AntiDDosParser.add_cleaning_access_pos_arg(parser)
        # pb.AntiDDosParser.add_app_type_arg(parser)
        return parser

    def take_action(self, args):
        client = self.app.client_manager.antiddos

        if args.enable_l7 and not args.http_request_rate:
            raise argparse.ArgumentTypeError(
                'argument --http-request-rate is required '
                'when CC defence protection is enabled'
            )

        if not args.enable_l7 and args.http_request_rate:
            raise argparse.ArgumentTypeError(
                'argument --http-request-rate only effect '
                'when CC defence protection is enabled'
            )

        floating_ip = client.antiddos.find(args.floating_ip)
        # issue 8, cleaning-pos fixed to 8, app-type fixed to 1
        traffic_pos = pb.AntiDDosParser.get_traffic_pos_id(
            args.maximum_service_traffic)
        http_request_pos = pb.AntiDDosParser.get_http_request_pos_id(
            args.http_request_rate)
        task = client.antiddos.open_antiddos(floating_ip.floating_ip_id,
                                             args.enable_l7,
                                             traffic_pos,
                                             http_request_pos,
                                             8,
                                             1)

        return 'Request Received, task id: ' + task['task_id']


class CloseAntiDDos(command.Command):
    _description = _("Close AntiDDos of floating IP")

    def get_parser(self, prog_name):
        parser = super(CloseAntiDDos, self).get_parser(prog_name)
        pb.AntiDDosParser.add_floating_ip_arg(parser)
        return parser

    def take_action(self, args):
        client = self.app.client_manager.antiddos
        floating_ip = client.antiddos.find(args.floating_ip)
        task = client.antiddos.close_antiddos(floating_ip.floating_ip_id)
        return 'Request Received, task id: ' + task['task_id']


class ShowAntiDDos(command.ShowOne):
    _description = _("Display AntiDDos settings of floating IP")

    def get_parser(self, prog_name):
        parser = super(ShowAntiDDos, self).get_parser(prog_name)
        pb.AntiDDosParser.add_floating_ip_arg(parser)
        return parser

    def take_action(self, args):
        client = self.app.client_manager.antiddos
        _antiddos = client.antiddos.find(args.floating_ip)
        # if user pass ip, we should reload antiddos object
        if _antiddos.floating_ip_id != args.floating_ip:
            _antiddos = client.antiddos.get_antiddos(_antiddos.floating_ip_id)

        if 'status' in _antiddos.original and _antiddos.status == 'notConfig':
            raise exceptions.ClientException(
                'You have not config antiddos for this floating ip yet.'
            )
        else:
            if not _antiddos.enable_L7:
                columns = resource.AntiDDos.show_column_names[:-1]
            else:
                columns = resource.AntiDDos.show_column_names
            return columns, _antiddos.get_display_data(columns)


class SetAntiDDos(command.Command):
    _description = _("Update AntiDDos settings of floating IP")

    def get_parser(self, prog_name):
        parser = super(SetAntiDDos, self).get_parser(prog_name)
        pb.AntiDDosParser.add_floating_ip_arg(parser)
        pb.AntiDDosParser.add_enable_l7_arg(parser)
        pb.AntiDDosParser.add_maximum_service_traffic_arg(parser)
        pb.AntiDDosParser.add_http_request_rate_arg(parser)
        # pb.AntiDDosParser.add_cleaning_access_pos_arg(parser)
        # pb.AntiDDosParser.add_app_type_arg(parser)
        return parser

    def take_action(self, args):
        client = self.app.client_manager.antiddos
        if not args.enable_l7 and args.http_request_rate:
            raise argparse.ArgumentTypeError(
                'argument --http-request-rate only effect '
                'when CC defence protection is enabled'
            )

        floating_ip = client.antiddos.find(args.floating_ip)

        # issue 8, cleaning-pos fixed to 8, app-type fixed to 1
        traffic_pos = pb.AntiDDosParser.get_traffic_pos_id(
            args.maximum_service_traffic)
        http_request_pos = pb.AntiDDosParser.get_http_request_pos_id(
            args.http_request_rate)
        task = client.antiddos.update_antiddos(floating_ip.floating_ip_id,
                                               args.enable_l7,
                                               traffic_pos,
                                               http_request_pos,
                                               8,
                                               1)

        if isinstance(task, br.StrWithMeta):
            raise exceptions.ClientException(
                'this floating ip already has the same configuration'
            )
        return 'Request Received, task id: ' + task['task_id']


class ShowAntiDDosTask(command.ShowOne):
    _description = _("Display antiddos related task details")

    def get_parser(self, prog_name):
        parser = super(ShowAntiDDosTask, self).get_parser(prog_name)
        parser.add_argument(
            'task_id',
            metavar='<task id>',
            help=_("AntiDDos setting task id")
        )
        return parser

    def take_action(self, args):
        client = self.app.client_manager.antiddos
        task = client.antiddos.get_task_status(args.task_id)
        columns = resource.AntiDDosTask.show_column_names
        return columns, task.get_display_data(columns)


class ListAntiDDosStatus(command.Lister):
    _description = _("List AntiDDos status")

    def get_parser(self, prog_name):
        parser = super(ListAntiDDosStatus, self).get_parser(prog_name)
        parser.add_argument(
            "--status",
            choices=resource.AntiDDos.status_list,
            help=_("list AntiDDos with status")
        )
        parser.add_argument(
            "--ip",
            help=_("list AntiDDos with the ip (eg: 110.110.)")
        )
        p.BaseParser.add_limit_option(parser)
        p.BaseParser.add_offset_option(parser)
        return parser

    def take_action(self, args):
        client = self.app.client_manager.antiddos
        data = client.antiddos.list(status=args.status,
                                    ip=args.ip,
                                    limit=args.limit,
                                    offset=args.offset)
        columns = resource.AntiDDos.list_column_names
        return columns, (r.get_display_data(columns) for r in data)


class ShowAntiDDosStatus(command.ShowOne):
    _description = _("Display AntiDDos status of floating ip")

    def get_parser(self, prog_name):
        parser = super(ShowAntiDDosStatus, self).get_parser(prog_name)
        pb.AntiDDosParser.add_floating_ip_arg(parser)
        return parser

    def take_action(self, args):
        manager = self.app.client_manager.antiddos.antiddos
        floating_ip = manager.find(args.floating_ip)
        status = manager.get_antiddos_status(floating_ip.floating_ip_id)
        columns = resource.AntiDDosStatus.show_column_names
        return columns, status.get_display_data(columns)


class ListAntiDDosDailyReport(command.Lister):
    _description = _("List AntiDDos report(every 5min) of past 24h")

    def get_parser(self, prog_name):
        parser = super(ListAntiDDosDailyReport, self).get_parser(prog_name)
        pb.AntiDDosParser.add_floating_ip_arg(parser)
        return parser

    def take_action(self, args):
        manager = self.app.client_manager.antiddos.antiddos
        floating_ip = manager.find(args.floating_ip)
        reports = manager.get_antiddos_daily_report(floating_ip.floating_ip_id)
        columns = resource.AntiDDosDailyReport.list_column_names
        return columns, (r.get_display_data(columns) for r in reports)


class ListAntiDDosLogs(command.Lister):
    _description = _("List AntiDDos logs(every 5min) of past 24h")

    def get_parser(self, prog_name):
        parser = super(ListAntiDDosLogs, self).get_parser(prog_name)
        pb.AntiDDosParser.add_floating_ip_arg(parser)
        p.BaseParser.add_limit_option(parser)
        p.BaseParser.add_offset_option(parser)
        p.BaseParser.add_sortdir_option(parser)
        return parser

    def take_action(self, args):
        # TODO(Woo) no data in test env, need to test later
        manager = self.app.client_manager.antiddos.antiddos
        floating_ip = manager.find(args.floating_ip)
        logs = manager.get_antiddos_daily_logs(
            floating_ip.floating_ip_id, args.sort_dir, args.limit, args.offset
        )
        columns = resource.AntiDDosLog.list_column_names
        data = (r.get_display_data(columns, formatter=r.formatter)
                for r in logs)
        return columns, data


class ListAntiDDosWeeklyReport(command.ShowOne):
    _description = _("List AntiDDos weekly protection statistics")

    def get_parser(self, prog_name):
        parser = super(ListAntiDDosWeeklyReport, self).get_parser(prog_name)
        parser.add_argument(
            '--start-date',
            metavar='<start-date>',
            required=False,
            type=parsetypes.date_type,
            help=_("start date (yyyy-MM-dd)")
        )
        return parser

    def take_action(self, args):
        manager = self.app.client_manager.antiddos.antiddos
        report = manager.get_antiddos_weekly_report(args.start_date)
        columns = resource.AntiDDosWeeklyReport.show_column_names
        formatter = resource.AntiDDosWeeklyReport.formatter
        output = report.get_display_data(columns, formatter=formatter)
        return columns, output
