# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import os
import glob
import tempfile
from path import path
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

import hgapi
from jinja2 import Template
from sphinx.application import Sphinx

from trytond.config import config
from trytond.model import ModelView
from trytond.modules import create_graph
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, StateAction,\
    Button

trytond_doc_path = config.get('documentation', 'trytond_doc_path',
    default=os.path.join(tempfile.mkdtemp(), 'trytond_doc'))
trytond_doc_url = config.get('documentation', 'trytond_doc_url',
    default='https://bitbucket.org/trytonspain/trytond-doc')
config_template = config.get('documentation', 'config_template',
    default=os.path.join(os.path.dirname(__file__), 'conf.py.jinja'))
build_lang = config.get('documentation', 'lang', default='es')
build_folder = config.get('documentation', 'root',
    default=tempfile.mkdtemp())
output_root = config.get('documentation', 'root',
    default=config.get('web', 'root'))
output_folder = config.get('documentation', 'folder',
    default='documentation')
public_url = config.get('documentation', 'public_url',
    default='http://localhost:8000')


__all__ = ['BuildDocumentationStart', 'BuildDocumentation',
    'OpenDocumentation']


class BuildDocumentationStart(ModelView):
    'Build Documentation Start'
    __name__ = 'documentation.build.start'


class BuildDocumentation(Wizard):
    'Build Documentation'
    __name__ = 'documentation.build'
    _sphinx_app = None

    start = StateView('documentation.build.start',
        'documentation.build_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Build', 'build', 'tryton-ok', default=True),
            ])
    build = StateTransition()

    @classmethod
    def __register__(cls, *args, **kwargs):
        super(BuildDocumentation, cls).__register__(*args, **kwargs)
        # XXX: Update doc on every upgrade?
        # cls.build_doc()

    def do_build(self, action):
        self.build_doc()
        return action, {}

    def transition_build(self):
        self.build_doc()
        return 'end'

    @classmethod
    def build_doc(cls):
        cls.update_trytond_doc()
        cls.fill_build_content()
        cls.make_doc()

    @classmethod
    def update_trytond_doc(cls):
        if not os.path.exists(trytond_doc_path):
            hgapi.hg_clone(trytond_doc_url, trytond_doc_path)
        repo = hgapi.Repo(trytond_doc_path)
        repo.hg_pull(trytond_doc_url)
        revision = repo.hg_branch()
        repo.hg_update(revision)

    @classmethod
    def get_documentation_modules(cls):
        pool = Pool()
        Module = pool.get('ir.module')
        modules = Module.search([('state', '=', 'installed')])
        graph = create_graph([module.name for module in modules])[0]
        return [m.name for m in graph]

    @classmethod
    def build_config_file(cls):
        with open(config_template) as f:
            template = Template(f.read())
        config_file = os.path.join(build_folder, 'conf.py')
        with open(config_file, 'w') as f:
            f.write(template.render(**cls.get_config_template_context()))

    @classmethod
    def get_config_template_context(cls):
        tryton_cfg = ConfigParser()
        filename = os.path.join(os.path.dirname(__file__), 'tryton.cfg')
        tryton_cfg.readfp(open(filename))
        version = dict(tryton_cfg.items('tryton')).get('version', '0.0.1')
        major_version, minor_version, _ = version.split('.', 2)
        return {
            'VERSION': '%s.%s' % (major_version, minor_version),
            'INSTALLED_MODULES': cls.get_documentation_modules(),
            }

    @classmethod
    def fill_build_content(cls):
        modules = os.path.join(os.path.dirname(__file__), '..')
        cls.create_symlinks(trytond_doc_path)
        cls.create_symlinks(modules)
        index = os.path.join(trytond_doc_path, 'index.rst')
        link = os.path.join(build_folder, 'index.rst')
        cls.make_link(index, link)

    @classmethod
    def create_symlinks(cls, origin):
        for module_doc_dir in glob.glob('%s/*/doc/%s' % (origin, build_lang)):
            module_name = str(path(module_doc_dir).parent.parent.basename())
            symlink = path(build_folder).joinpath(module_name)
            if not symlink.exists():
                path(build_folder).relpathto(
                    path(module_doc_dir)).symlink(symlink)

    @classmethod
    def make_link(cls, origin, destination):
        directory = os.path.dirname(destination)
        if not os.path.exists(destination):
            path(directory).relpathto(path(origin)).symlink(destination)

    @classmethod
    def make_doc(cls):
        db = Transaction().database.name
        dest = os.path.join(output_root, output_folder, db)
        doctree_dir = os.path.join(dest, '.doctrees')
        cls.build_config_file()
        # We must cache sphinx instance otherwise extensions are loaded
        # multiple times and duplicated references errors are raised.
        if cls._sphinx_app is None:
            cls._sphinx_app = Sphinx(
                build_folder, build_folder, dest, doctree_dir, 'html')
        cls._sphinx_app.build()


class OpenDocumentation(Wizard):
    'Open Documentation'
    __name__ = 'documentation.open'
    start = StateAction('documentation.act_open_documentation')

    def do_start(self, action):
        db = Transaction().database.name
        action['url'] = '%s/%s/%s/index.html' % (public_url, output_folder, db)
        return action, {}
