"""Regional NoSQL table inventory; no rows, schema, indexes or usage queries."""


def collect_nosql(call,add,compartment):
    # List summaries already provide all architecture fields. GetTable would
    # add schema/DDL and require read permissions without improving placement.
    for table in call('nosql','list_tables',compartment_id=compartment) or []:
        add(table,'nosql_table',compartment_id=getattr(table,'compartment_id',None) or compartment,
            lifecycle_state=getattr(table,'lifecycle_state',None),deployment_scope='regional')
