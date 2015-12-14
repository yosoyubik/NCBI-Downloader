metadata = {
    "sample_name": "",
    "group_name": "",
    "file_names": "",
    "sequencing_platform": "",
    "sequencing_type": "",
    "pre_assembled": "",
    "sample_type": "",
    "organism": "",
    "strain": "",
    "subtype": {},
    "country": "",
    "region": "",
    "city": "",
    "zip_code": "",
    "longitude": "",
    "latitude": "",
    "location_note": "",
    "isolation_source": "",
    "source_note": "",
    "pathogenic": "",
    "pathogenicity_note": "",
    "collection_date": "",
    "collected_by": "",
    "usage_restrictions": "",
    "release_date": "",
    "email_address": "",
    "notes": "",
    "batch": "true"
}

default = {
    "mandatory": [
        "pre_assembled",
        "sequencing_platform",
        "sequencing_type",
        "country",
        "isolation_source",
        "collection_date"
    ],
    "seed": {
        "pre_assembled": "no",
        "sample_type": "isolate",
        "organism": "",
        "pathogenic": "yes",
        "usage_restrictions": "public",
        "usage_delay": "0"
    }
}
