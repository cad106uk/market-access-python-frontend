import copy

from .forms.search import BarrierSearchForm
from interactions.models import Document

from utils.metadata import get_metadata
from utils.models import APIModel

import dateutil.parser


class Barrier(APIModel):
    def __init__(self, data):
        self.data = data
        metadata = get_metadata()

        self.id = data['id']
        self.code = data['code']
        self.title = data['barrier_title']
        self.product = data.get('product')
        self.location = metadata.get_location(
            data['export_country'],
            data['country_admin_areas']
        )

        if data.get('sectors'):
            self.sectors = [
                metadata.get_sector(sector_id)
                for sector_id in data['sectors']
            ]
        else:
            self.sectors = []

        if self.sectors:
            self.sector_names = [
                sector.get('name', "Unknown") for sector in self.sectors
            ]
        else:
            self.sector_names = ["All sectors"]
        status_code = str(data['status']['id'])
        self.status = metadata.get_status(status_code)
        self.problem = {
            'status': metadata.get_problem_status(self.problem_status),
            'description': data.get('problem_description')
        }
        self.priority = data['priority']
        self.reported_on = dateutil.parser.parse(data['reported_on'])
        self.modified_on = dateutil.parser.parse(data['modified_on'])
        self.status_date = dateutil.parser.parse(data['status']['date'])
        self.added_by = data.get('reported_by')
        self.date = {
            'reported': self.reported_on,
            'status': dateutil.parser.parse(data['status']['date']),
            'created': dateutil.parser.parse(data['created_on']),
        }
        self.types = [
            metadata.get_barrier_type(barrier_type)
            for barrier_type in data['barrier_types']
        ]
        self.eu_exit_related = metadata.get_eu_exit_related_text(
            data['eu_exit_related']
        )
        self.source = {
            'id': data.get('source'),
            'name': metadata.get_source(data.get('source')),
            'description': data.get('other_source'),
        }
        if 'companies' in self.data:
            self.companies = data['companies']

        if self.export_country:
            self.country = metadata.get_country(self.export_country)
            self.admin_area_ids = self.data['country_admin_areas']

            if self.admin_area_ids:
                self.admin_areas = metadata.get_admin_areas(
                    self.admin_area_ids
                )
            else:
                self.admin_areas = []

    def to_dict(self):
        return {
            'title': self.title,
            'priority': self.priority['code'],
            'description': self.problem_description,
            'problem_status': self.problem_status,
            'eu_exit_related': self.data['eu_exit_related'],
            'product': self.product,
            'source': self.data['source'],
            'other_source': self.data['other_source'],
            'status': self.status,
        }

    def get_sector_ids(self):
        return [sector['id'] for sector in self.sectors]

    def get_barrier_types(self):
        metadata = get_metadata()
        return [
            metadata.get_barrier_type(barrier_type)
            for barrier_type in self.data['barrier_types']
        ]

    @property
    def is_resolved(self):
        return self.status['id'] == '4'

    @property
    def is_partially_resolved(self):
        return self.status['id'] == '3'

    @property
    def is_open(self):
        return self.status['id'] == '2'

    @property
    def is_hibernated(self):
        return self.status['id'] == '5'


class Company(APIModel):
    def __init__(self, data):
        self.data = data
        self.created_on = dateutil.parser.parse(data['created_on'])

    def get_address_display(self):
        address_parts = [
            self.data['address'].get('line_1'),
            self.data['address'].get('line_2'),
            self.data['address'].get('town'),
            self.data['address'].get('county'),
            self.data['address'].get('postcode'),
            self.data['address'].get('country', {}).get('name'),
        ]
        address_parts = [part for part in address_parts if part]
        return ", ".join(address_parts)


class Assessment(APIModel):
    def __init__(self, data):
        self.data = data
        metadata = get_metadata()
        self.impact_text = metadata.get_impact_text(self.data.get('impact'))
        self.documents = [Document(document) for document in data['documents']]


class Watchlist:
    _readable_filters = None

    def __init__(self, name, filters, *args, **kwargs):
        self.name = name
        self.filters = filters

    def to_dict(self):
        return {
            'name': self.name,
            'filters': self.filters,
        }

    @property
    def readable_filters(self):
        if self._readable_filters is None:
            search_form = BarrierSearchForm(
                metadata=get_metadata(),
                data=self.filters,
            )
            search_form.full_clean()
            self._readable_filters = search_form.get_readable_filters()
        return self._readable_filters

    def get_api_params(self):
        """
        Transform watchlist filters into api parameters
        """
        filters = copy.deepcopy(self.filters)
        region = filters.pop('region', [])
        country = filters.pop('country', [])

        if country or region:
            filters['location'] = country + region

        if 'createdBy' in filters:
            created_by = filters.pop('createdBy')
            if '1' in created_by:
                filters['user'] = 1
            elif '2' in created_by:
                filters['team'] = 1

        filter_map = {
            'type': 'barrier_type',
            'search': 'text',
        }

        api_params = {}
        for name, value in filters.items():
            mapped_name = filter_map.get(name, name)
            if isinstance(value, list):
                api_params[mapped_name] = ",".join(value)
            else:
                api_params[mapped_name] = value

        return api_params
