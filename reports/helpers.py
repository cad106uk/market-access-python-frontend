import json
from datetime import datetime

import requests

from reports.constants import FormSessionKeys
from reports.forms.new_report_barrier_location import HasAdminAreas
from reports.forms.new_report_barrier_sectors import SectorsAffected
from reports.forms.new_report_barrier_status import BarrierStatuses
from reports.models import Report
from utils.api.client import MarketAccessAPIClient

from django.conf import settings

# Barrier fields and The corresponding step in add a barrier journey.
# fields = (
#     "id",
#     "code",
#     "problem_status",       # Step 1.1 - Status
#     "is_resolved",          # Step 1.2 - Status
#     "resolved_date",        # Step 1.2 - Status
#     "resolved_status",      # Step 1.2 - Status
#     "status",               # n/a - Barrier status (e.g.: unfinished, open , dormant, etc...)
#     "status_summary",       # n/a
#     "status_date",          # n/a
#     # ==============================
#     "export_country",       # Step 2 - Location - UUID
#     "country_admin_areas",  # Step 2 - Location - LIST of UUIDS
#     # ==============================
#     "sectors_affected",     # Step 3 - Sectors - BOOL
#     "all_sectors",          # Step 3 - Sectors - BOOL
#     "sectors",              # Step 3 - Sectors - LIST of UUIDS
#     # ==============================
#     "product",              # Step 4 - About - STR - Affected product, service, investment
#     "source",               # Step 4 - About - STR - choices as per metadata.barrier_source
#     "other_source",         # Step 4 - About - STR - only applicable if the above source filed was "OTHER"
#     "barrier_title",        # Step 4 - About - STR - name of the barrier
#     "problem_description",
#     "next_steps_summary",
#     "eu_exit_related",      # Step 4 - About - INT - metadata.get_eu_exit_related_text (TODO: probs need another helper for choices)
#     "progress",
#     "created_by",
#     "created_on",
#     "modified_by",
#     "modified_on",
# )


class SessionKeys:
    """
    Set of session keys to be used at report forms to help with draft barrier data management.
    """
    meta_mapping = {
        FormSessionKeys.PROBLEM_STATUS: "problem_status_form_data",
        FormSessionKeys.STATUS: "status_form_data",
        FormSessionKeys.LOCATION: "location_form_data",
        FormSessionKeys.HAS_ADMIN_AREAS: "has_admin_areas_form_data",
        FormSessionKeys.ADMIN_AREAS: "admin_areas_form_data",
        FormSessionKeys.SELECTED_ADMIN_AREAS: "selected_admin_areas",
        FormSessionKeys.SECTORS_AFFECTED: "sectors_affected",
        FormSessionKeys.SECTORS: "sectors",
        FormSessionKeys.ABOUT: "about",

    }
    attr_mapping = {}

    @classmethod
    def __init__(cls, infix=""):
        """Set up session key mapping to reflect context."""
        for key, value in cls.meta_mapping.items():
            new_value = f"draft_barrier_{infix}_{value}"
            setattr(cls, key, new_value)
            cls.attr_mapping[key] = new_value

    @classmethod
    def flush(cls, session):
        """Removes session keys as per mapping."""
        for key, value in cls.attr_mapping.items():
            session.pop(value, None)


class ReportFormGroup:
    """
    Used to handle field values for draft barriers.
    Form values are stored in the user session:
     - session key naming pattern for DRAFT barriers: "draft_barrier_<UUID>_session_key"
     - session key naming pattern for UNSAVED barriers: "draft_barrier__session_key"
    """
    def __init__(self, session, barrier_id=None):
        self.session = session
        self.session_keys = None
        self.barrier = None
        self.barrier_id = barrier_id
        self.client = MarketAccessAPIClient(session.get("sso_token"))
        self.init_session_keys()

    # STATUS
    # ==================================
    @property
    def problem_status_form(self):
        return self.get(FormSessionKeys.PROBLEM_STATUS, {})

    @problem_status_form.setter
    def problem_status_form(self, value):
        self.set(FormSessionKeys.PROBLEM_STATUS, value)

    @property
    def status_form(self):
        return self.get(FormSessionKeys.STATUS, {})

    @status_form.setter
    def status_form(self, value):
        self.set(FormSessionKeys.STATUS, value)

    # LOCATION
    # ==================================
    @property
    def location_form(self):
        return self.get(FormSessionKeys.LOCATION, {})

    @location_form.setter
    def location_form(self, value):
        self.set(FormSessionKeys.LOCATION, value)

    @property
    def has_admin_areas(self):
        return self.get(FormSessionKeys.HAS_ADMIN_AREAS, {})

    @has_admin_areas.setter
    def has_admin_areas(self, value):
        self.set(FormSessionKeys.HAS_ADMIN_AREAS, value)

    @property
    def selected_admin_areas(self):
        """
        Selected admin areas
        :return: STR - comma separated UUIDs
        """
        return self.get(FormSessionKeys.SELECTED_ADMIN_AREAS, "")

    @selected_admin_areas.setter
    def selected_admin_areas(self, value):
        self.set(FormSessionKeys.SELECTED_ADMIN_AREAS, value)

    @property
    def selected_admin_areas_as_list(self):
        areas = self.selected_admin_areas
        if areas:
            areas = areas.replace(" ", "").split(",")
        return areas or []

    def remove_selected_admin_area(self, admin_area_id):
        admin_areas = self.selected_admin_areas_as_list
        admin_areas.remove(admin_area_id)
        self.selected_admin_areas = ', '.join(admin_areas)

    # SECTORS
    # ==================================
    @property
    def sectors_affected(self):
        return self.get(FormSessionKeys.SECTORS_AFFECTED, {})

    @sectors_affected.setter
    def sectors_affected(self, value):
        self.set(FormSessionKeys.SECTORS_AFFECTED, value)

    @property
    def selected_sectors(self):
        """
        Selected sectors
        :return: STR - comma separated UUIDs
        """
        return self.get(FormSessionKeys.SECTORS, "")

    @selected_sectors.setter
    def selected_sectors(self, value):
        self.set(FormSessionKeys.SECTORS, value)

    @property
    def selected_sectors_as_list(self):
        sectors = self.selected_sectors
        if sectors:
            sectors = sectors.replace(" ", "").split(",")
        return sectors or []

    def selected_sectors_generator(self, metadata):
        """
        Returns selected sectors if any as a GENERATOR.

        :metadata: data from utils.metadata.get_metadata()
        :return: TUPLE, (BOOL|has selected sectors, GENERATOR|selected sectors)
        """
        sector_ids = self.selected_sectors
        if sector_ids == "all":
            sectors = (("all", "All sectors"),)
        else:
            sectors = (
                (sector["id"], sector["name"])
                for sector in metadata.get_sectors(sector_ids)
            )
        return (sector_ids != ""), sectors

    def remove_selected_sector(self, sector_id):
        sectors = self.selected_sectors_as_list
        sectors.remove(sector_id)
        self.selected_sectors = ', '.join(sectors)

    # ABOUT
    # ==================================
    @property
    def about_form(self):
        return self.get(FormSessionKeys.ABOUT, {})

    @about_form.setter
    def about_form(self, value):
        self.set(FormSessionKeys.ABOUT, value)

    # UTILS
    # ==================================
    @property
    def session_key_infix(self):
        infix = ""
        if self.barrier_id:
            infix = str(self.barrier_id)
        return infix

    def load_from_session(self):
        pass

    def get(self, session_key, default=None):
        """Retrieving the value stored in a session key"""
        if not session_key:
            # If for whatever reason the session_key is falsy fall back to default
            return default

        key = getattr(self.session_keys, session_key)
        return self.session.get(key, default)

    def set(self, session_key, value):
        """Assigning a value to a session key"""
        if not session_key:
            return

        key = getattr(self.session_keys, session_key)
        if key:
            self.session[key] = value

    def init_session_keys(self):
        if self.session_keys:
            self.session_keys.flush(self.session)
        self.session_keys = SessionKeys(self.session_key_infix)

    def get_problem_status_form_data(self):
        return {
            "status": str(self.barrier.data.get("problem_status"))
        }

    def get_status_form_data(self):
        """Returns DICT - extract status form data from barrier.data"""
        data = {
            "status": "",
            "resolved_month": None,
            "resolved_year": None,
            "part_resolved_month": None,
            "part_resolved_year": None,
            "is_resolved": None,
        }

        if not self.barrier:
            return data

        data["is_resolved"] = self.barrier.data.get("is_resolved")
        data["status"] = str(self.barrier.data.get("resolved_status"))

        if data["status"] in (BarrierStatuses.RESOLVED, BarrierStatuses.PARTIALLY_RESOLVED):
            date_string = self.barrier.data.get("resolved_date")
            if date_string:
                date = datetime.strptime(date_string, '%Y-%m-%d')
                if data["status"] == BarrierStatuses.RESOLVED:
                    data["resolved_month"] = date.month
                    data["resolved_year"] = date.year
                elif data["status"] == BarrierStatuses.PARTIALLY_RESOLVED:
                    data["part_resolved_month"] = date.month
                    data["part_resolved_year"] = date.year
        else:
            data["status"] = BarrierStatuses.UNRESOLVED

        return data

    def get_location_form_data(self):
        return {
            "country": self.barrier.data.get("export_country")
        }

    def get_has_admin_areas_form_data(self):
        data = {"has_admin_areas": None}
        if self.barrier.data["country_admin_areas"]:
            data["has_admin_areas"] = HasAdminAreas.NO
        else:
            data["has_admin_areas"] = HasAdminAreas.YES
        return data

    def get_sectors_affected_form_data(self):
        data = {"sectors_affected": None}
        # TODO, only set this if progress is not "NOT STARTED" for "Sectors affected"
        if self.barrier.data["sectors_affected"]:
            data["sectors_affected"] = SectorsAffected.YES
        else:
            data["sectors_affected"] = SectorsAffected.NO
        return data

    def get_selected_sectors(self):
        """Helper to extract selected sectors from barrier data and preload the form."""
        all_sectors = (self.barrier.data.get("all_sectors") is True)
        if all_sectors:
            selected_sectors = "all"
        else:
            selected_sectors = ', '.join(self.barrier.data.get("sectors"))
        return selected_sectors

    def get_about_form(self):
        data = {
            "barrier_title": self.barrier.data.get("barrier_title"),
            "product": self.barrier.data.get("product"),
            "source": self.barrier.data.get("source"),
            "other_source": self.barrier.data.get("other_source"),
            "eu_exit_related": self.barrier.data.get("eu_exit_related"),
        }
        return data

    def update_session_keys(self):
        """
        Update value of each session key, based on data from self.barrier.data
        """
        self.problem_status_form = self.get_problem_status_form_data()
        self.status_form = self.get_status_form_data()
        self.location_form = self.get_location_form_data()
        self.has_admin_areas = self.get_has_admin_areas_form_data()
        self.selected_admin_areas = ', '.join(self.barrier.data.get("country_admin_areas"))
        self.sectors_affected = self.get_sectors_affected_form_data()
        self.selected_sectors = self.get_selected_sectors()
        self.about_form = self.get_about_form()

    def update_context(self, barrier):
        self.barrier = barrier
        self.barrier_id = barrier.id
        self.init_session_keys()
        self.update_session_keys()

    def prepare_payload(self):
        """Combined payload of multiple steps (Status & Location)"""
        payload = {
            "problem_status": self.problem_status_form.get("status"),
            "is_resolved": self.status_form.get("is_resolved"),
            "resolved_date": self.status_form.get("resolved_date"),
            "resolved_status": self.status_form.get("status"),
            "export_country": self.location_form.get("country"),
            "country_admin_areas": self.selected_admin_areas_as_list,
        }

        if payload["resolved_status"] == BarrierStatuses.UNRESOLVED:
            payload["is_resolved"] = False
            payload["resolved_status"] = None
            payload["resolved_date"] = None

        return payload

    def prepare_payload_sectors(self):
        all_sectors = (self.selected_sectors == "all")
        sectors = ()
        sectors_affected = self.sectors_affected.get("sectors_affected")

        if sectors_affected == SectorsAffected.YES:
            if not all_sectors:
                sectors = self.selected_sectors_as_list
        else:
            all_sectors = False

        payload = {
            "sectors_affected": sectors_affected,
            "all_sectors": all_sectors,
            "sectors": sectors,
        }

        return payload

    def prepare_payload_about(self):
        payload = self.about_form
        return payload

    def _update_barrier(self, payload):
        # TODO: this really should be in the client, but that doesn't handle JSON :/
        token = self.session.get("sso_token")
        url = f'{settings.MARKET_ACCESS_API_URI}reports/{self.barrier_id}'
        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json',
            'X-User-Agent': '',
            'X-Forwarded-For': '',
        }
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        barrier_data = json.loads(response.text)
        return Report(barrier_data)

    def save(self, payload=None):
        """Create or update a (report) barrier."""
        payload = payload or self.prepare_payload()
        if self.barrier_id:
            barrier = self._update_barrier(payload=payload)
        else:
            barrier = self.client.reports.create(**payload)
        self.update_context(barrier)