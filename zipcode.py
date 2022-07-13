import pgeocode
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

nomi = pgeocode.Nominatim('us')
dist = pgeocode.GeoDistance('us')

MI_TO_KM = 1.60934
KM_TO_MI = 0.621371


class Distance():

    @classmethod
    def get_location_matches(cls, location, users, max_distance):
        """given a location and list of potental matches with user max distance
        return a list of zipcodes that match the criteria.
        ZIPCODES MUST BE IN STRING FORMAT."""

        max_kilos = int(max_distance) * MI_TO_KM
        matches = [match for match in users if (dist.query_postal_code(location, match["location"])) <= max_kilos]

        return matches
