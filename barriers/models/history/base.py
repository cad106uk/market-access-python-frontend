from utils.diff import diff_match_patch
from utils.metadata import MetadataMixin
from utils.models import APIModel

import dateutil.parser


class BaseHistoryItem(MetadataMixin, APIModel):
    _metadata = None
    _new_value = None
    _old_value = None
    modifier = ""

    @property
    def date(self):
        return dateutil.parser.parse(self.data["date"])

    @property
    def new_value(self):
        if self._new_value is None:
            self._new_value = self.get_value(self.data["new_value"])
        return self._new_value

    @property
    def old_value(self):
        if self._old_value is None:
            self._old_value = self.get_value(self.data["old_value"])
        return self._old_value

    @property
    def diff(self):
        dmp = diff_match_patch()
        diffs = dmp.diff_main(self.old_value or "", self.new_value or "")
        dmp.diff_cleanupSemantic(diffs)
        return dmp.diff_prettyHtml(diffs)

    def get_value(self, value):
        return value


class GenericHistoryItem(BaseHistoryItem):
    """
    HistoryItem class used when unable to find a match for the model and field
    """

    @property
    def field_name(self):
        return self.field.replace("_", " ").title()
