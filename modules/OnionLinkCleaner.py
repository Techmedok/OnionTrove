import re

def Clean(onionlinks):
    CleanedOnionLinks = []

    for onionlink in onionlinks:
        if not re.match(r'^\w+://', onionlink):
            onionlink = 'http://' + onionlink

        if re.search(r'(https?://.*?\.onion)', onionlink):
            if "http://" in onionlink:
                newurl = "http://" + onionlink.split("://")[1].split("/")[0].rstrip('/')
                CleanedOnionLinks.append(newurl)
            else:
                newurl = "https://" + onionlink.split("://")[1].split("/")[0].rstrip('/')
                CleanedOnionLinks.append(newurl)

    return CleanedOnionLinks