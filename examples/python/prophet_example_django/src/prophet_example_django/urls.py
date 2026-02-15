from __future__ import annotations

from pathlib import Path
import sys

from django.http import HttpResponse
from django.urls import path

ROOT = Path(__file__).resolve().parents[2]
GEN_SRC = ROOT / "gen" / "python" / "src"
if str(GEN_SRC) not in sys.path:
    sys.path.insert(0, str(GEN_SRC))

from generated.django_urls import urlpatterns as generated_urlpatterns

from .app import initialize_generated_runtime

initialize_generated_runtime()

urlpatterns = [
    *generated_urlpatterns,
    path("healthz", lambda request: HttpResponse("ok")),
]
