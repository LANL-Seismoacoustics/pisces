import unittest

import nose.tools as t
import sqlalchemy as sa
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

from pisces import db_connect
import pisces.schema.util as util
import pisces.schema.kbcore as kb


class TestPiscesMeta(unittest.TestCase):
    def setUp(self):
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

    def test_qualified_tablename_abstract(self):

        class Sitechan(kb.Sitechan):
            __tablename__ = 'test.sitechan'

        self.assertTrue(Sitechan.__table__.name == 'sitechan')
        self.assertTrue(Sitechan.__table__.schema == 'test')
        self.assertTrue(Sitechan.__tablename__ == 'sitechan')

    @unittest.skip("Not yet implemented.")
    def test_reflect_qualified_tablename(self):
        """
        Reflect an actual schema-qualified database table.

        """

        class Site(util.ORMBase, DeferredReflection):
            __tablename__ = 'jkmacc.site'

        session = db_connect()
        Site.prepare(session.bind)

        self.assertTrue(Site.__tablename__ == 'site')
        self.assertTrue(Site.__table__.name == 'site')
        self.assertTrue(Site.__table__.schema == 'jkmacc')

    @unittest.skip("Not yet implemented.")
    def test_reflect_qualified_tablename_pk(self):
        pass

def test_normal_declarative():
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

    t.assert_true(Sitechan.__tablename__ == 'sitechan')
    t.assert_true(Sitechan.__table__.name == 'sitechan')

@unittest.skip("Not yet implemented.")
def test_reflected_declarative():
    from pisces.schema.util import PiscesMeta
    session = db_connect()
    Base = declarative_base(metaclass=PiscesMeta)
    class Site(Base, DeferredReflection):
        __tablename__ = 'site'
    Site.prepare(session.bind)

    t.assert_true(Site.__tablename__ == 'site')
    t.assert_true(Site.__table__.name == 'site')

@unittest.skip("Not yet implemented.")
def test_reflected_declarative_pk_override():
    from pisces.schema.util import PiscesMeta
    session = db_connect
    Base = declarative_base(metaclass=PiscesMeta)
    class Sitechan(Base, DeferredReflection):
        __tablename__ = 'sitechan'
        __primary_keys__ = ['chanid']
    Sitechan.prepare(session.bind)

    t.assert_true(Sitechan.__tablename__ == 'sitechan')
    t.assert_true(Sitechan.__table__.name == 'sitechan')
    t.assert_true('chanid' in Sitechan.__table__.primary_key)

def test_schema_declarative():
    from pisces.schema.util import PiscesMeta
    Base = declarative_base(metaclass=PiscesMeta)
    class Sitechan(Base):
        __tablename__ = 'testuser.sitechan'
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

    t.assert_true(Sitechan.__tablename__ == 'sitechan')
    t.assert_true(Sitechan.__table__.name == 'sitechan')
    t.assert_true(Sitechan.__table__.schema == 'testuser')

def test_abstract_declarative():
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

    class Sitechan(AbstractSitechan):
        __tablename__ = 'sitechan'

    t.assert_true(Sitechan.__tablename__ == 'sitechan')
    t.assert_true(Sitechan.__table__.name == 'sitechan')

def test_schema_abstract_declarative():
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

    class Sitechan(AbstractSitechan):
        __tablename__ = 'testuser.sitechan'

    t.assert_true(Sitechan.__tablename__ == 'sitechan')
    t.assert_true(Sitechan.__table__.name == 'sitechan')
    t.assert_true(Sitechan.__table__.schema == 'testuser')

def test_two_abstract_declarative():
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

    class Sitechan(AbstractSitechan):
        __tablename__ = 'sitechan'

    class JSitechan(AbstractSitechan):
        __tablename__ = 'testuser.sitechan'

    t.assert_true(Sitechan.__tablename__ == 'sitechan')
    t.assert_true(Sitechan.__table__.name == 'sitechan')
    t.assert_true(JSitechan.__tablename__ == 'sitechan')
    t.assert_true(JSitechan.__table__.name == 'sitechan')
    t.assert_true(JSitechan.__table__.schema == 'testuser')


if __name__ == '__main__':
    unittest.main()
