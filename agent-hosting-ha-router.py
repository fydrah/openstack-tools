#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Usage:
#
# $ export OS_XXXXX
# ...
#
# $ ./agent-hosting-ha-router.py <[json]|yaml|yml|table>
#
# >json
#
# >yaml|yml
#
# >table (requires terminaltables)
# +--------------------+--------------------------------------+----------------------------------+---------------------+
# | name               | id                                   | project                          | agents              |
# +--------------------+--------------------------------------+----------------------------------+---------------------+
# | router3            | 039ae521-0cdb-4b61-b7a5-97e333dcb35b | 68a93cc709b44de08cfd11e6bdac2b9b | - ha_state: active  |
# |                    |                                      |                                  |   host: osnet001    |
# |                    |                                      |                                  | - ha_state: standby |
# |                    |                                      |                                  |   host: osnet002    |
# |                    |                                      |                                  |                     |
# | router2            | 97d2ab1d-0cec-49d5-856f-0a1a3c9a5156 | 68a93cc709b44de08cfd11e6bdac2b9b | - ha_state: active  |
# |                    |                                      |                                  |   host: osnet001    |
# |                    |                                      |                                  | - ha_state: standby |
# |                    |                                      |                                  |   host: osnet002    |
# |                    |                                      |                                  |                     |
# | router1            | f1c23964-7025-4ded-ab14-992f636b3485 | 8f77be9ac1ef49b6ad033e84000ec182 | - ha_state: null    |
# |                    |                                      |                                  |   host: osnet001    |
# +--------------------+--------------------------------------+----------------------------------+---------------------+



import sys
import json
import yaml
try:
    from terminaltables import AsciiTable
    NO_TABLE=False
except ImportError:
    NO_TABLE=True
    pass

try:
    import openstack
except ImportError:
    print('[ERR] `openstacksdk` required')
    sys.exit(1)

try:
    CONN = openstack.connect()
except Exception as ex:
    print('[ERR] Probably missing OS_* environment variables: %s' % ex)

def list_routers_on_l3_agents():
    res = []
    for rt in CONN.list_routers():
        it = {
            'router': {
                'id': rt.id,
                'name': rt.name,
                'project': rt.project_id,
                'active': 0
            },
            'agents': []
        }
        ags = CONN.network.routers_hosting_l3_agents(rt)
        for ag in ags:
            # HA States: ['active', 'standby', 'standalone']
            ha_state = 'standalone'
            if ag.ha_state is not None :
                ha_state = ag.ha_state
            if ha_state in ['active', 'standalone']:
                it['router']['active'] += 1
            it['agents'].append({
                'host': ag.host,
                'ha_state': ha_state,
            })
        res.append(it)
    return res

def main(output):
    if output == 'json':
        print(json.dumps(list_routers_on_l3_agents()))
    elif output in ['yaml', 'yml']:
        print(yaml.safe_dump(list_routers_on_l3_agents()))
    elif output == 'table':
        if NO_TABLE:
            print('[ERR] Cannot use table rendre, missing `terminaltables`')
            sys.exit(1)
        tbl = [
            ['name', 'id', 'project', 'active', 'agents'],
        ]
        for line in list_routers_on_l3_agents():
            tbl.append([
                line['router']['name'],
                line['router']['id'],
                line['router']['project'],
                line['router']['active'],
                yaml.safe_dump(line['agents'])
            ])
        table = AsciiTable(tbl)
        print(table.table)
    else:
        print('[ERR] %s is not a valid output. Choices: [table], json, yaml|yml' % output)
        sys.exit(1)

if __name__ == '__main__':
    if not NO_TABLE:
        output = 'table'
    else:
        output = 'json'
    if len(sys.argv) > 1:
        output = sys.argv[1]
    main(output)
