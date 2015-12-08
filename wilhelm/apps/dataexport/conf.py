from django.conf import settings

data_export_timestamp_format = '%y%m%d%H%M%S'
human_readable_date_format = '%B %d, %Y'
human_readable_time_format = '%H:%M:%S'
isoformat = '%Y-%m-%d %H:%M:%S' # YYYY-MM-DD HH:MM:SS 
indent_level = 2
data_archives_cache = settings.DATA_ARCHIVES_CACHE
tarball_compression_method = 'bz2' # bz2 or gz

hash_algorithms = dict(sha1 = ('sha1', 'SHA-1', 'sha1sum'),
                       sha256 = ('sha256', 'SHA-256', 'sha256sum'))

default_hash_algorithm = hash_algorithms['sha256']

# Name of the file of checksum info.
tarball_checksum = 'checksum_%s.txt' % default_hash_algorithm[0]

readme_txt = 'readme.txt'
license_txt = 'licence.txt' # Go with British English spelling.

textwidth = 200

odbl_license_template = """
This {DATA_NAME} ({UID}) is made available under the Open Database License:
http://opendatacommons.org/licenses/odbl/1.0/. 

Any rights in individual contents of the database are licensed under the Database Contents License:
http://opendatacommons.org/licenses/dbcl/1.0/.

"""

readme_template = dict(
    introduction = """ This directory contains the data from experiment
    "{EXPERIMENT_NAME}" that was collected from the online behavioural
    experiment hosted at
    {EXPERIMENT_URL}""",
    timestamp = """This data-set was exported on {EXPORT_DATE}
    at {EXPORT_TIME} and is the complete data-set from the experiment as of
    that time.""",
    unique_id = """ The unique ID for the data-set is {UNIQUE_ID} """,
    permalink = """
    The permalink for the data-set is
    {PERMALINK}
    """,
    checksum_info = """ The {HASH_ALGORITHM} hashes of all the data files in
    this data-set are listed in the file {CHECKSUM_FILENAME}. These can be used to
    check integrity of each file (using the {SHASUM} utility). """.format(
        HASH_ALGORITHM=default_hash_algorithm[1],
        CHECKSUM_FILENAME=tarball_checksum,
        SHASUM=default_hash_algorithm[2]
    ))
