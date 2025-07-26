import math
from typing import Optional
from config import LEIGH_COORDINATES, config

# Constants pulled from config
MAX_DISTANCE_MILES = config.LOCATION_RADIUS_MILES
MIN_SALARY_PER_HOUR = config.MIN_SALARY_PER_HOUR
MIN_SALARY_PER_YEAR = config.MIN_SALARY_PER_YEAR
MAX_CV_SCORE_FOR_NO_SALARY = getattr(config, "MAX_CV_SCORE_FOR_NO_SALARY", 9.0)
MIN_COMPANY_RATING = getattr(config, "MIN_COMPANY_RATING", 6.0)

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in miles between two lat/lon points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

def is_within_radius(job_lat: float, job_lon: float,
                     center_lat: float = LEIGH_COORDINATES["lat"],
                     center_lon: float = LEIGH_COORDINATES["lon"],
                     max_distance: float = MAX_DISTANCE_MILES) -> bool:
    return haversine(job_lat, job_lon, center_lat, center_lon) <= max_distance

def is_part_time(job_type: Optional[str]) -> bool:
    if not job_type:
        return False
    jt = job_type.lower()
    return "part‑time" in jt or "part time" in jt

def salary_meets_threshold(salary_hourly: Optional[float] = None,
                           salary_yearly: Optional[float] = None,
                           cv_score: float = 0.0) -> bool:
    if salary_hourly is not None:
        return salary_hourly >= MIN_SALARY_PER_HOUR
    if salary_yearly is not None:
        return salary_yearly >= MIN_SALARY_PER_YEAR
    # If no salary info, require CV score cutoff
    return cv_score >= MAX_CV_SCORE_FOR_NO_SALARY

def company_rating_meets(rating: Optional[float]) -> bool:
    if rating is None:
        return True
    return rating >= MIN_COMPANY_RATING

def passes_filters(job: dict, cv_score: float,
                   center_lat: float = LEIGH_COORDINATES["lat"],
                   center_lon: float = LEIGH_COORDINATES["lon"]) -> bool:
    """
    job: {
        'latitude': float,
        'longitude': float,
        'job_type': str,
        'salary_hourly': Optional[float],
        'salary_yearly': Optional[float],
        'company_rating': Optional[float],
    }
    """
    if not is_within_radius(job["latitude"], job["longitude"], center_lat, center_lon):
        return False
    if not is_part_time(job.get("job_type")):
        return False
    if not salary_meets_threshold(job.get("salary_hourly"), job.get("salary_yearly"), cv_score):
        return False
    if not company_rating_meets(job.get("company_rating")):
        return False
    return True
