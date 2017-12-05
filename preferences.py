

# List of subscribers that should be notified if the preferences change.
_subscribers = []

# The preferences file parsed as JSON.
_preferences = None


def load(file_path):
    # Load the preferences file.
    with open(file_path, encoding='utf-8') as data_file:
        contents = data_file.read()
        # Remove all comments that start with "//".
        contents = re.sub('//.*[\r\n]*', '', contents, 0, re.M)
        # Remove blank lines.
        contents = re.sub('^\s*[\r\n]*', '', contents, 0, re.M)
        # Parse the file as JSON.
        global preferences
        preferences = json.loads(contents)
	# Watch the preferences file for changes.
	#QtCore.QFileSystemWatcher


def subscribe(subscriber):
	pass


def get(pref_name):
	return preferences[pref_name]
