import os

from nmk.completion import ConfigCompleter
from nmk.parser import NmkParser
from tests.utils import NmkTester


class TestConfig(NmkTester):
    def test_config_sample(self):
        # Dump config loaded from file
        self.nmk(
            "config_sample.yml", extra_args=["--print", "someString", "--print", "someInt", "--print", "someBool", "--print", "someList", "--print", "someDict"]
        )
        self.check_logs(
            'Config dump: { "someString": "abcd", "someInt": 1234, "someBool": false, "someList": [ "abc", "def" ], "someDict": { "adc": "def", "ghi": "jkl" } }'
        )

        # In quiet mode, for coverage
        self.nmk(
            "config_sample.yml",
            extra_args=["--print", "someString", "--print", "someInt", "--print", "someBool", "--print", "someList", "--print", "someDict", "-q"],
        )

    def test_config_merge(self):
        # Dump config loaded from file (with override)
        self.nmk(
            "config_override.yml",
            extra_args=["--print", "someString", "--print", "someInt", "--print", "someBool", "--print", "someList", "--print", "someDict"],
        )
        self.check_logs(
            'Config dump: { "someString": "def", "someInt": 567, "someBool": true, "someList": [ "abc", "def", "ghi" ], "someDict": { "adc": "foo", "ghi": "jkl", "bar": "zzz" } }'
        )

    def test_config_invalid_fragment(self):
        self.nmk("simplest.yml", extra_args=["--config", '{"foo:'], expected_error="Invalid Json fragment for --config option: ")

    def test_config_invalid_json(self):
        self.nmk("simplest.yml", extra_args=["--config", '["foo"]'], expected_error='Config option is neither a json object nor a K=V string: ["foo"]')

    def test_config_override(self):
        self.nmk(
            "config_sample.yml",
            extra_args=[
                "--print",
                "someString",
                "--print",
                "someInt",
                "--print",
                "someBool",
                "--print",
                "someList",
                "--print",
                "someDict",
                "--config",
                '{"someInt":65}',
                "--config",
                str({}),
                "--config",
                "someString=foo",
            ],
        )
        self.check_logs(
            'Config dump: { "someString": "foo", "someInt": 65, "someBool": false, "someList": [ "abc", "def" ], "someDict": { "adc": "def", "ghi": "jkl" } }'
        )

    def test_config_override_bad_type(self):
        self.nmk("config_sample.yml", extra_args=["--config", '{"someList":65}'], expected_error="Unexpected type change for config someList (list --> int)")

    def test_config_invalid_resolver(self):
        self.nmk("config_invalid_resolver.yml", expected_error="While loading {project}: Invalid class qualified name: AbcDef (missing separator: .)")

    def test_config_unknown_module_resolver(self):
        self.nmk("config_unknown_resolver.yml", expected_error="While loading {project}: Can't instantiate class foo.bar.SomeResolver:")

    def test_config_unknown_class_resolver(self):
        self.nmk(
            "config_unknown_class_resolver.yml",
            expected_error="While loading {project}: Can't instantiate class tests.failling_resolvers.UnknownResolver: Can't find class UnknownResolver in module tests.failling_resolvers",
        )

    def test_config_exception_resolver(self):
        self.nmk(
            "config_exception_resolver.yml",
            expected_error="While loading {project}: Can't instantiate class tests.failling_resolvers.FaillingResolver: Can't instantiate abstract class FaillingResolver",
        )

    def test_config_bad_type_resolver(self):
        self.nmk(
            "config_bad_type_resolver.yml",
            expected_error="While loading {project}: Unexpected type for loaded class tests.failling_resolvers.BadTypeResolver: got BadTypeResolver, expecting NmkConfigResolver subclass",
        )

    def test_config_str_resolver(self):
        self.nmk("config_str_resolver.yml", extra_args=["--print", "someResolved"])
        self.check_logs('Config dump: { "someResolved": "my dynamic value" }')

    def test_config_list_resolver(self):
        self.nmk("config_list_resolver.yml", extra_args=["--print", "someResolved"])
        self.check_logs('Config dump: { "someResolved": [ 1, 2 ] }')

    def test_config_lying_resolver(self):
        self.nmk(
            "config_lying_resolver.yml",
            extra_args=["--print", "someResolved"],
            expected_error="Error occurred while resolving config someResolved: Invalid type returned by resolver: got str, expecting int",
        )

    def test_config_throwing_resolver(self):
        self.nmk(
            "config_throwing_resolver.yml",
            extra_args=["--print", "someResolved"],
            expected_error="While loading {project}: Error occurred while getting type for config someResolved: Always failed!",
        )

    def test_config_volatile_resolver(self):
        self.nmk("config_volatile_resolver.yml", extra_args=["--print", "someResolved"])
        self.check_logs(
            'Config dump: { "someResolved": { "0": { "someList": [ 1, 2 ], "someDict": { "a": 1, "b": 2 }, "someVolatile": 1, "someNonVolatile": 1 }, "1": { "someList": [ 1, 2 ], "someDict": { "a": 1, "b": 2 }, "someVolatile": 2, "someNonVolatile": 1 } } }'
        )

    def test_config_resolver_with_python_path(self):
        self.nmk("config_python_path_resolver.yml", extra_args=["--print", "someResolved"])
        self.check_logs('Config dump: { "someResolved": "my dynamic value from python path" }')

    def test_config_resolver_with_unknown_python_path(self):
        self.nmk("config_unknown_python_path_resolver.yml", expected_error="While loading {project}: Contributed python path is not found:")

    def test_config_recursive_resolve(self):
        self.nmk("config_recursive.yml", extra_args=["--print", "someConfig"])
        self.check_logs('Config dump: { "someConfig": "_abc/ghi/def_123_" }')

    def test_config_unknown_reference(self):
        self.nmk(
            "config_unknown_config_ref.yml",
            extra_args=["--print", "someConfig"],
            expected_error="Unknown 'someUnknownVar' config referenced from 'someConfig' config",
        )

    def test_config_recursive_reference(self):
        self.nmk(
            "config_recursive_config_ref.yml",
            extra_args=["--print", "someConfig"],
            expected_error="Cyclic string substitution: resolving (again!) 'someConfig' config from 'someOtherVar' config",
        )

    def test_config_override_final(self):
        self.nmk("config_override_final.yml", expected_error="While loading {project}: Can't override final config BASEDIR")

    def test_config_builtin(self):
        self.nmk(
            "simplest.yml", extra_args=["--print", "ROOTDIR", "--print", "CACHEDIR", "--print", "PROJECTDIR", "--print", "PROJECTFILES", "--print", "BASEDIR"]
        )
        self.check_logs(
            f'Config dump: {{ "BASEDIR": "", "ROOTDIR": "{self.test_folder}", "CACHEDIR": "{self.test_folder}/.nmk", "PROJECTDIR": "{self.templates_root}", "PROJECTFILES": [ "{self.template("simplest.yml")}" ] }}'
        )

    def test_config_dot_no_dict(self):
        self.nmk(
            "config_dot_no_dict.yml",
            extra_args=["--print", "tryDotRef"],
            expected_error="Doted reference from tryDotRef used for someString value, which is not a dict",
        )

    def test_config_dot_empty_segment(self):
        self.nmk(
            "config_dot_empty_segment.yml",
            extra_args=["--print", "tryDotRef"],
            expected_error="Empty doted reference segment from tryDotRef for someDict value",
        )

    def test_config_dot_unknown_key(self):
        self.nmk(
            "config_dot_unknown_key.yml",
            extra_args=["--print", "tryDotRef"],
            expected_error="Unknown dict key abc in doted reference from tryDotRef for someDict value",
        )

    def test_config_dot_ok(self):
        self.nmk("config_dot_ok.yml", extra_args=["--print", "tryDotRef"])
        self.check_logs(f'Config dump: {{ "tryDotRef": "_{os.environ["HOME"]}_" }}')

    def test_config_completion(self):
        # With final ones
        configs = ConfigCompleter()(
            "", None, None, NmkParser().parse(["--root", self.test_folder.as_posix(), "-p", self.template("config_sample.yml").as_posix()])
        )
        assert len(configs) == 5 + 7  # 5 provided one + 7 built-ins
        assert all(t in configs for t in ["someInt", "someString", "someBool", "someList", "someDict"])

        # Without final ones
        configs = ConfigCompleter(False)(
            "", None, None, NmkParser().parse(["--root", self.test_folder.as_posix(), "-p", self.template("config_sample.yml").as_posix()])
        )
        assert len(configs) == 5 + 1  # 5 provided one + 1 non-final built-in
        assert all(t in configs for t in ["someInt", "someString", "someBool", "someList", "someDict"])
