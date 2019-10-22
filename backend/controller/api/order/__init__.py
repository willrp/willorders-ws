from .select_by_slug import selectBySlugNS
from .select_by_user import selectByUserNS
from .insert import insertNS
from .delete import deleteNS

NSOrder = [
    selectBySlugNS,
    selectByUserNS,
    insertNS,
    deleteNS
]
