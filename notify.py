import requests
import json
from flask import current_app as app
import extensions as ext

# TODO move this to external data format later once debugged
# targets MUST be a list (or other iterable) or None
notify_types = {
    "case_incoming": {
        "targets": None,
        "msg_base": "INCOMING PATIENT ETA {eta_mins} MINUTES"
    },
    "case_acknowledged": {
        "targets": None,
        "msg_base": "ACKNOWLEDGED BY {hospital_name},"
    },
    "case_arrived": {
        "targets": None,
        "msg_base": "ACTIVE PATIENT ARIVAL IN ED"
    },
    "likely_lvo": {
        "targets": None,
        "msg_base": "LIKELY LVO, ECR NOT CONFIRMED"
    },
    "ct_ready": {
        "targets": None,
        "msg_base": "CT {ct_num}, READY"
    },
    "ctb_completed": {
        "targets": None,
        "msg_base": "CTB Completed"
    },
    "do_cta_ctp": {
        "targets": None,
        "msg_base": "PROCEED TO CTA/CTP"
    },
    "ecr_activated": {
        "targets": None,
        "msg_base": "ECR ACTIVATED"
    },
    "case_completed": {
        "targets": None,
        "msg_base": "CASE COMPLETED"
    },
}

def add_message(notify_type, case_id, args=None):
    """ Add notification with arguments.

    Args:
        notify_type: a notification type as specified in notify_types dict. 
        case_id: ID of case which will used to get arguments.
        args: dictionary of arguments for packaging with package_message.
    """

    header = {"Content-Type": "application/json; charset=utf-8",
              "Authorization": "Basic {}".format(app.config['OS_REST_API_KEY'])}

    # TODO Handle if required args not present
    msg_prefix = "{initials} {age}{gender} -- "
    packaged = package_message(case_id, args)
    msg = (msg_prefix + notify_types[notify_type]['msg_base']).format(**packaged)

    targets = notify_types[notify_type]['targets']

    if targets == None:
        payload = {"app_id": app.config['OS_APP_ID'],
                   "included_segments": ["All"],
	           "contents": {"en": msg}}
    # TODO Test filter-specific messages once roles implemented
    else:
        payload = {"app_id": config['OS_APP_ID'],
                   "filters": filterize(targets),
	           "contents": {"en": msg}}

    print(json.dumps(payload))

    req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
    print(req.reason, req.text, req.json()) # debugging

def filterize(targets):
    filter_list = []

    for target in targets:
        filter_list.extend([
            {"field": "tag", "key": "role", "relation": "=", "value": target},
            {"operator": "OR"}
        ])

    del filter_list[-1] # remove last OR operator

    return filter_list

def package_message(case_id, args):
    case_info = ext.get_all_case_info_(case_id)
    info = {}
    # Just to simplify, assume first name and last name are each one word
    # Will probably have to modify later to account for two-word first or last names
    info['initials'] = case_info['first_name'][0] + case_info['last_name'][0]
    # TODO calculate age based on dob returned
    info['age'] = case_info['dob']
    info['gender'] = case_info['gender']
    # TODO Be exclusive with which arguments are provided based on notification type
    if args:
        info['eta_mins'] = 30 if 'eta_mins' in args.keys() else None# PLACEHOLDER until this is clarified how to calculate
        info['hospital_name'] = 'Austin' if 'hospital_name' in args.keys() else None# PLACEHOLDER until hospital id and hospital name linked
        info['ct_num'] = args['ct_num'] if 'ct_num' in args.keys() else None
    return info
