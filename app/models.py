import graphene
from sys import stderr

from . import app, mongo
from .views import list_users_page


class User(graphene.ObjectType):
    _id = graphene.ID()
    username = graphene.String()
    password = graphene.String()
    email = graphene.String()


class WatchedPage(graphene.ObjectType):
    _id = graphene.ID()
    owner_name = graphene.String()
    page_name = graphene.String()
    url = graphene.String()
    authentication = graphene.String()
    interval = graphene.Int()


class Query(graphene.ObjectType):
    user = graphene.List(User,
                        _id=graphene.ID(),
                        username=graphene.String()
                        )
    watched_page = graphene.List(WatchedPage,
                        _id=graphene.ID(),
                        owner_name=graphene.String(),
                        page_name=graphene.String(),
                        url=graphene.String()
                        )

    @graphene.resolve_only_args
    def resolve_user(self, username=None):
        query_dict = {}
        if username is not None:
            query_dict['username'] = username
        result = list(mongo.db.users.find(query_dict))
        if result is not None:
            # EUREKA!@#! -- time needed to realise that dicts are unpackable
            # and we don't need a specialized mongodb-graphene module to
            # automagically change dicts into instances of classes: 1h45min
            return [User(**kwargs) for kwargs in result] # BTW python magic
        return None

    @graphene.resolve_only_args
    def resolve_watched_page(self, _id=None, owner_name=None, page_name=None, url=None):
        query_dict = {}
        if _id is not None:
            query_dict['_id'] = _id
        if owner_name is not None:
            query_dict['owner_name'] = owner_name
        if page_name is not None:
            query_dict['page_name'] = page_name
        if url is not None:
            query_dict['url'] = url

        result = list(mongo.db.watched_pages.find(query_dict))
        if result is not None:
            return [WatchedPage(**kwargs) for kwargs in result]
        return None


schema = graphene.Schema(query=Query, auto_camelcase=False)
