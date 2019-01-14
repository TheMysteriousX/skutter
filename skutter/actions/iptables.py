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

    _targets = {'accept': 'ACCEPT',
                'drop': 'DROP',
                }

    def __init__(self, conf: dict) -> None:
        log.debug('IPTables plugin initialising with config: %s', conf)

        self._table4 = iptc.Table(self._tables[conf['table'] if 'table' in conf else 'filter'])
        self._table6 = iptc.Table6(self._tables[conf['table'] if 'table' in conf else 'filter'])
        log.debug('iptables._table4 == %s', self._table4)
        log.debug('iptables._table6 == %s', self._table6)

        chain = conf['chain'] if 'chain' in conf else 'INPUT'

        self._chain4 = iptc.Chain(self._table4, chain)
        self._chain6 = iptc.Chain(self._table6, chain)
        log.debug('iptables._chain4 == %s', chain)
        log.debug('iptables._chain6 == %s', chain)

        if 'target' in conf:
            self._target = self._targets[conf['target']]
        else:
            self._target = None
        log.debug('iptables._target == %s', self._target)

        if 'ports' in conf['match']:
            self._ports = conf['match']['ports']
        else:
            self._ports = None
        log.debug('iptables._ports == %s', self._ports)

        if 'protocol' in conf['match']:
            self._proto = conf['match']['protocol']
        else:
            self._proto = None
        log.debug('iptables._proto == %s', self._proto)

        if 'sources' in conf['match']:
            self._sources = [ip_network(ip) for ip in conf['match']['sources']]
        else:
            self._sources = None
        log.debug('iptables._sources == %s', self._sources)

        if 'destinations' in conf['match']:
            self._dests = [ip_network(ip) for ip in conf['match']['sources']]
        else:
            self._dests = None
        log.debug('iptables._dests == %s', self._dests)

        self._rule4 = iptc.Rule()
        self._rule6 = iptc.Rule6()

        self._uuids: List[str] = []

        try:
            self.rule_builder()
        except ValueError as e:
            log.error('An error was encountered while initialising the IPTables plugin')
            log.debug(e)
            raise e

    def rule_builder(self):
        if not Configuration.get('v6-only'):
            self.rule_builder4()

        self.rule_builder6()

    def rule_builder4(self):
        self._rule4.target = iptc.Target(self._rule4, self._target)
        log.debug('Set rule4 target: %s', self._rule4.target)

        if self._proto:
            self._rule4.protocol = self._proto
            log.debug('Set rule4 proto: %s', self._rule4.protocol)

        if self._ports:
            self._rule4.create_match(self._rule4.protocol).dport = self._ports
            log.debug('Set rule4 dport: %s', self._ports)

        if self._sources:
            self._rule4.src = ','.join([ip.compressed for ip in self._sources if isinstance(ip, IPv4Network)])
            log.debug('Set rule4 src: %s', self._rule4.src)

        if self._dests:
            self._rule4.dst = ','.join([ip.compressed for ip in self._dests if isinstance(ip, IPv4Network)])
            log.debug('Set rule4 src: %s', self._rule4.dst)

        uid = str(uuid.uuid4())
        m = self._rule4.create_match("comment")
        m.comment = f"{Configuration.get('self-uuid')}-{uid}"

        self._uuids.append(uid)

        log.info('Built IPTables rule: %s', self._rule4)

    def rule_builder6(self):
        self._rule6.target = iptc.Target(self._rule6, self._target)
        log.debug('Set rule6 target: %s', self._rule6.target)

        if self._proto:
            self._rule6.protocol = self._proto
            log.debug('Set rule6 proto: %s', self._rule6.protocol)

        if self._ports:
            self._rule6.create_match(self._rule6.protocol).dport = self._ports
            log.debug('Set rule6 dport: %s', self._ports)

        if self._sources:
            self._rule6.src = ','.join([ip.compressed for ip in self._sources if isinstance(ip, IPv6Network)])
            log.debug('Set rule6 src: %s', self._rule6.src)

        if self._dests:
            self._rule6.dst = ','.join([ip.compressed for ip in self._dests if isinstance(ip, IPv6Network)])
            log.debug('Set rule6 src: %s', self._rule6.dst)

        uid = str(uuid.uuid4())
        m = self._rule6.create_match("comment")
        m.comment = f"{Configuration.get('self-uuid')}-{uid}"

        self._uuids.append(uid)

        log.info('Built IPTables rule: %s', self._rule6)

    def del_rule4(self, rule: iptc.Rule) -> bool:
        log.info("Deleting rule4 from chain")
        if self._chain4 is not None:
            try:
                return self._chain4.delete_rule(rule)
            except iptc.ip4tc.IPTCError:
                log.error('Unable to remove rule - rule may have been removed outside of skutter')
                return False

    def del_rule6(self, rule: iptc.Rule6) -> bool:
        log.info("Deleting rule6 from chain")
        if self._chain6 is not None:
            try:
                return self._chain6.delete_rule(rule)
            except iptc.ip6tc.IPTCError:
                log.error('Unable to remove rule - rule may have been removed outside of skutter')
                return False

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
            for rule in self._chain4.rules:
                for match in rule.matches:
                    if match.name == 'comment':
                        if match.parameters['comment'].startswith(Configuration.get('self-uuid')):
                            self.del_rule4(rule)

    def cleanup6(self):
        log.info("Cleaning up all rule6 with comment prefix: %s", Configuration.get('self-uuid'))

        if self._chain6 is not None:
            for rule in self._chain6.rules:
                for match in rule.matches:
                    if match.name == 'comment':
                        if match.parameters['comment'].startswith(Configuration.get('self-uuid')):
                            self.del_rule6(rule)

