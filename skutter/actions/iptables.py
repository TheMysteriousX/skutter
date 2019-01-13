import logging
import os
import uuid

from ipaddress import ip_network, IPv4Network, IPv6Network
from typing import List

from skutter import Configuration
from skutter.actions import ActionBase

log = logging.getLogger(__name__)

try:
    import iptc
except FileNotFoundError as e:
    log.error('Unable to load iptc, are we actually running on Linux?')

    if 'SKUTTER' in os.environ:
        log.critical('Mocking iptc for development use')
        log.critical('If you see this message in production, do not use the service and notify the developers')

        from unittest.mock import MagicMock
        iptc = MagicMock()
    else:
        raise e


class IPTables(ActionBase):
    _tables = {'filter': iptc.Table.FILTER,
               'mangle': iptc.Table.MANGLE,
               'nat': iptc.Table.NAT,
               'security': iptc.Table.SECURITY
               }

    _uuids: List[str] = []

    _table4 = None
    _table6 = None

    _rule4 = None
    _rule6 = None

    _chain4 = None
    _chain6 = None

    _target = None

    _ports = None
    _protos = None
    _sources = None
    _dests = None
    _interfaces = None
    _state = None

    def __init__(self, conf: dict) -> None:
        self._table4 = iptc.Table(self._tables[conf['table'] if 'table' in conf else 'filter'])
        self._table6 = iptc.Table6(self._tables[conf['table'] if 'table' in conf else 'filter'])

        chain = conf['chain'] if 'chain' in conf else 'INPUT'
        self.chain4 = iptc.Chain(self._table4, chain)
        self.chain6 = iptc.Chain(self._table6, chain)

        if 'proto' in conf['match']:
            self._target = conf['target']

        if 'ports' in conf['match']:
            self._ports = conf['match']['ports']

        if 'ports' in conf['match']:
            self._proto = conf['match']['protocol']

        if 'sources' in conf['match']:
            self._sources = [ip_network(ip) for ip in conf['match']['sources']]

        if 'destinations' in conf['match']:
            self._dests = [ip_network(ip) for ip in conf['match']['sources']]

        self._rule4 = iptc.Rule()
        self._rule6 = iptc.Rule6()

        log.info('Built IPTables rule: %s', self._rule4)
        log.info('Built IPTables rule: %s', self._rule6)

    def rule_builder(self):
        if not Configuration.get('v6-only'):
            self.rule_builder4()

        self.rule_builder6()

    def rule_builder4(self):
        with self._rule4 as r:
            r.target = iptc.Target(r, self._target)

            if self._proto:
                r.protocol = self._proto

            if self._ports:
                r.dport = ','.join(self._ports)

            if self._sources:
                r.src = ','.join([ip.compressed for ip in self._sources if isinstance(IPv4Network, ip)])

            if self._dests:
                r.dst = ','.join([ip.compressed for ip in self._dests if isinstance(IPv4Network, ip)])

    def rule_builder6(self):
        with self._rule6 as r:
            r.target = iptc.Target(r, self._target)

            if self._proto:
                r.protocol = self._proto

            if self._ports:
                r.dport = ','.join(self._ports)

            if self._sources:
                r.src = ','.join([ip.compressed for ip in self._sources if isinstance(IPv6Network, ip)])

            if self._dests:
                r.dst = ','.join([ip.compressed for ip in self._dests if isinstance(IPv6Network, ip)])

            uid = str(uuid.uuid4())
            m = r.create_match("comment")
            m.comment(f"{Configuration.get('self-uuid')}-{uid}")

            self._uuids.append(uid)

    def del_rule4(self, rule: iptc.Rule) -> bool:
        log.info("Deleting rule4 from chain")
        if self._chain4 is not None:
            return self._chain4.delete_rule(rule)

    def del_rule6(self, rule: iptc.Rule6) -> bool:
        log.info("Deleting rule6 from chain")
        if self._chain6 is not None:
            return self._chain6.delete_rule(rule)

    def insert_rule4(self, rule: iptc.Rule) -> bool:
        log.info("Inserting rule4 into chain")
        if self._chain4 is not None:
            return self._chain4.insert_rule(rule)

    def insert_rule6(self, rule: iptc.Rule6) -> bool:
        log.info("Inserting rule6 into chain")
        if self._chain6 is not None:
            return self._chain6.insert_rule(rule)

    def do(self):
        self.insert_rule4(self._rule4)
        self.insert_rule6(self._rule6)

    def undo(self):
        self.del_rule4(self._rule4)
        self.del_rule6(self._rule6)

    def cleanup4(self):
        log.info("Cleaning up all rule4 with comment prefix: %s", Configuration.get('self-uuid'))

        if self._chain4 is not None:
            for rule in self._chain4:
                for match in rule.matches:
                    if match.name == 'comment':
                        if match.parameters['comment'].startswith(Configuration.get('self-uuid')):
                            self.del_rule4(rule)

    def cleanup6(self):
        log.info("Cleaning up all rule6 with comment prefix: %s", Configuration.get('self-uuid'))

        if self._chain6 is not None:
            for rule in self._chain6:
                for match in rule.matches:
                    if match.name == 'comment':
                        if match.parameters['comment'].startswith(Configuration.get('self-uuid')):
                            self.del_rule6(rule)

    def __del__(self):
        self.cleanup4()
        self.cleanup6()
