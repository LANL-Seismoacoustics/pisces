"""
Test for general schema utility functions and classes.

"""
import pytest
import sqlalchemy as sa
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

from pisces import db_connect
import pisces.schema.util as util


@pytest.fixture(scope='function')
def abstract_sitechan():
    """ An abstract table inheriting from PiscesMeta. """
    from pisces.schema.util import PiscesMeta
    Base = declarative_base(metaclass=PiscesMeta)
    class AbstractSitechan(Base):
        __abstract__ = True
        @declared_attr
        def __table_args__(cls):
            return (sa.UniqueConstraint('sta','chan','ondate'),
                    sa.PrimaryKeyConstraint('chanid'))
        sta = sa.Column(sa.String(6))
        chan = sa.Column(sa.String(8))
        ondate = sa.Column(sa.Integer)
        chanid = sa.Column(sa.Integer)
        offdate = sa.Column(sa.Integer)
        ctype = sa.Column(sa.String(4))
        edepth = sa.Column(sa.Float(24))
        hang = sa.Column(sa.Float(24))
        vang = sa.Column(sa.Float(24))
        descrip = sa.Column(sa.String(50))
        lddate = sa.Column(sa.DateTime)

    return AbstractSitechan

@pytest.fixture(scope='function')
def concrete_sitechan():
    """ A concrete table inheriting directly from PiscesMeta. """
    from pisces.schema.util import PiscesMeta
    Base = declarative_base(metaclass=PiscesMeta)
    class Sitechan(Base):
        __tablename__ = 'sitechan'
        __table_args__ = (sa.UniqueConstraint('sta','chan','ondate'),
                            sa.PrimaryKeyConstraint('chanid'))
        sta = sa.Column(sa.String(6))
        chan = sa.Column(sa.String(8))
        ondate = sa.Column(sa.Integer)
        chanid = sa.Column(sa.Integer)
        offdate = sa.Column(sa.Integer)
        ctype = sa.Column(sa.String(4))
        edepth = sa.Column(sa.Float(24))
        hang = sa.Column(sa.Float(24))
        vang = sa.Column(sa.Float(24))
        descrip = sa.Column(sa.String(50))
        lddate = sa.Column(sa.DateTime)

    return Sitechan

class TestPiscesMeta:
    def test_qualified_tablename_abstract(self, abstract_sitechan):
        """ Tables inheriting from abstract tables properly split schema.name """

        class Sitechan(abstract_sitechan):
            __tablename__ = 'test.sitechan'

        assert Sitechan.__table__.name == 'sitechan'
        assert Sitechan.__table__.schema == 'test'
        assert Sitechan.__tablename__ == 'sitechan'

    def test_unqualified_tablename_abstract(self, abstract_sitechan):
        """ Tables inheriting from abstract tables properly split name """

        class Sitechan(abstract_sitechan):
            __tablename__ = 'sitechan'

        assert Sitechan.__table__.name == 'sitechan'
        assert Sitechan.__table__.schema == None
        assert Sitechan.__tablename__ == 'sitechan'

    @pytest.mark.skip("Not yet implemented.")
    def test_reflect_qualified_tablename(self):
        """
        Reflect an actual schema-qualified database table.

        """

        class Site(util.ORMBase, DeferredReflection):
            __tablename__ = 'jkmacc.site'

        session = db_connect()
        Site.prepare(session.bind)

        assert Site.__tablename__ == 'site'
        assert Site.__table__.name == 'site'
        assert Site.__table__.schema == 'jkmacc'

    @pytest.mark.skip("Not yet implemented.")
    def test_reflect_qualified_tablename_pk(self):
        pass

    def test_qualified_tablename_concrete(self, concrete_sitechan):
        assert concrete_sitechan.__tablename__ == 'sitechan'
        assert concrete_sitechan.__table__.name == 'sitechan'
        assert concrete_sitechan.__table__.schema == None

    @pytest.mark.skip("Not yet implemented.")
    def test_reflected_declarative(self):
        from pisces.schema.util import PiscesMeta
        session = db_connect()
        Base = declarative_base(metaclass=PiscesMeta)
        class Site(Base, DeferredReflection):
            __tablename__ = 'site'
        Site.prepare(session.bind)

        assert Site.__tablename__ == 'site'
        assert Site.__table__.name == 'site'

    @pytest.mark.skip("Not yet implemented.")
    def test_reflected_declarative_pk_override(self):
        from pisces.schema.util import PiscesMeta
        session = db_connect
        Base = declarative_base(metaclass=PiscesMeta)
        class Sitechan(Base, DeferredReflection):
            __tablename__ = 'sitechan'
            __primary_keys__ = ['chanid']
        Sitechan.prepare(session.bind)

        assert Sitechan.__tablename__ == 'sitechan'
        assert Sitechan.__table__.name == 'sitechan'
        assert 'chanid' in Sitechan.__table__.primary_key


    def test_two_abstract(self, abstract_sitechan):
        """ No errors when multiple tables are declared in same scope. """

        class Sitechan(abstract_sitechan):
            __tablename__ = 'sitechan'

        class JSitechan(abstract_sitechan):
            __tablename__ = 'testuser.sitechan'

        assert Sitechan.__tablename__ == 'sitechan'
        assert Sitechan.__table__.name == 'sitechan'
        assert JSitechan.__tablename__ == 'sitechan'
        assert JSitechan.__table__.name == 'sitechan'
        assert JSitechan.__table__.schema == 'testuser'