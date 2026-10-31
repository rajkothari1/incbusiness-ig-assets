# IncBusiness routine kit

Copies of the IncBusiness scripts the cloud routines run (source of truth: the site repo). The Instagram carousel routine runs:

    python3 kit/scripts/business-models/bm_carousel.py carousel.json out

Update these whenever the originals change.

The Instagram news reel routine (docs/news-reel-playbook.md on the site) runs:

    python3 kit/scripts/instagram/news_reel.py lines WORK
    python3 kit/scripts/instagram/news_reel.py build WORK
