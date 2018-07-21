import iptc


class IPTables(object):
    _tables = {'filter': iptc.Table.FILTER,
               'mangle': iptc.Table.MANGLE,
               'nat': iptc.Table.NAT,
               'security': iptc.Table.SECURITY
               }
    _chain = ''

    _rule = None

    def __init__(self, table: str = 'FILTER', chain: str = 'INPUT') -> None:
        self._table = iptc.Table(self._tables[table])
        self._chain = chain

        iptc.Rule()

    def add_rule(self) -> bool:
        return self.insert_rule('D')

    def del_rule(self) -> bool:
        return self.insert_rule('A')

    def insert_rule(self, action: str) -> bool:
        if self._rule.commit():
            return True
