from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from core.models import License  

class LicenseCheckMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        # Skip admin and login URLs
        if request.path.startswith("/FsrlxfOd8UwZQNxPcaJTdT8neaGTLG0Q/") or request.path.startswith("/admin/"):
            return self.get_response(request)
        
        try:
            license_obj = License.objects.filter(active=True).order_by("-id").first()
            if not license_obj or not license_obj.is_valid:
                return HttpResponseForbidden("🚫 License expired. Contact admin.")
        except Exception as e:
            # Log the error if you have logging set up
            # logger.error(f"License check error: {e}")
            # Allow access if there's a database error during startup
            pass
        
        return self.get_response(request)