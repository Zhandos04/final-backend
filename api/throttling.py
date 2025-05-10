from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class CustomUserRateThrottle(UserRateThrottle):
    rate = '100/minute'

class CustomAnonRateThrottle(AnonRateThrottle):
    rate = '20/minute'