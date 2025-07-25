import math




# Constants — tweak these in config.py later for flexibility
MAX_DISTANCE_MILES = 5
MIN_SALARY_PER_HOUR = 11
MIN_SALARY_PER_YEAR = 17500
MIN_CV_SCORE = 7.0
MAX_CV_SCORE_FOR_NO_SALARY = 9.0
MIN_COMPANY_RATING = 6.0

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in miles between two lat/lon points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2) + math.cos(phi1) * math.cos(phi2) *
(math.sin(dlambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

def is_within_radius(job_lat, job_lon, center_lat, center_lon,
max_distance=MAX_DISTANCE_MILES):
    return haversine(job_lat, job_lon, center_lat, center_lon) <= max_distance

def is_part_time(job_type):
    if not job_type:
        return False
    return 'part-time' in job_type.lower() or 'part time' in job_type.lower()

def salary_meets_threshold(salary_hourly=None, salary_yearly=None, cv_score=0):
    if salary_hourly is not None:
        return salary_hourly >= MIN_SALARY_PER_HOUR
    if salary_yearly is not None:
        return salary_yearly >= MIN_SALARY_PER_YEAR
    # If no salary info, accept only if CV score is high enough
    return cv_score >= MAX_CV_SCORE_FOR_NO_SALARY

def company_rating_meets(rating):
    if rating is None:
        # If no rating, accept the job anyway (can be tweaked)
        return True
    return rating >= MIN_COMPANY_RATING

def passes_filters(job, cv_score, center_lat, center_lon):
    """
    job dict expected keys:
    - latitude, longitude (float)
    - job_type (str)
    - salary_hourly (float or None)
    - salary_yearly (float or None)
    - company_rating (float or None)
    cv_score: float (0-10)
    """
    if not is_within_radius(job['latitude'], job['longitude'], center_lat,
center_lon):
        return False
    if not is_part_time(job.get('job_type', '')):
        return False
    if not salary_meets_threshold(job.get('salary_hourly'),
job.get('salary_yearly'), cv_score):
        return False
    if not company_rating_meets(job.get('company_rating')):
        return False
    return True
