from pathlib import Path

from nmk._internal.completion import ConfigCompleter
from nmk._internal.parser import NmkParser
from tests.utils import NmkTester


# On Windows, json serialization escapes the \ in paths
def json_serialized_path(in_path: Path) -> str:
    return str(in_path).replace("\\", "\\\\")


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
                "--print",
                "otherDict",
            ],
        )
        self.check_logs(
            'Config dump: { "someString": "def", '
            + '"someInt": 567, '
            + '"someBool": true, '
            + '"someList": [ "abc", "def", "ghi" ], '
            + '"someDict": { "adc": "foo", "ghi": "jkl", "bar": "zzz" }, '
            + '"otherDict": { "subList": [ "a", "b", "c" ], "subDict": { "a": 1, "b": 3, "c": 5 } } }'
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

    def test_config_resolvers(self):
        # Test resolvers:
        #  - string one with some parameters
        #  - bool one
        self.prepare_project("config_resolvers.yml")
        self.nmk("config_resolvers_override.yml", extra_args=["--print", "someResolved", "--print", "someBool", "--print", "someOverridableBool"])
        self.check_logs('Config dump: { "someResolved": "my dynamic value", "someBool": true, "someOverridableBool": false }')

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

    def test_config_resolver_with_overriding_python_path(self):
        self.nmk("config_python_path_resolver_override.yml", extra_args=["--print", "someResolved"])
        self.check_logs('Config dump: { "someResolved": "my dynamic value from overridden python path" }')

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

    def test_config_relative_path_reference(self):
        self.nmk("config_relative_path_ref.yml", extra_args=["--print", "someConfig", "--print", "someListRef", "--print", "someDictRef"])
        self.check_logs(
            f'Config dump: {{ "someConfig": [ ".nmk", "{json_serialized_path(self.templates_root / ".nmk")}" ], '  # NOQA:B028
            + '"someListRef": [ ".nmk" ], '
            + '"someDictRef": { "foo": ".nmk" } }'
        )

    def test_config_relative_path_invalid_reference(self):
        self.nmk(
            "config_relative_path_invalid_ref.yml",
            extra_args=["--print", "someConfig"],
            expected_error="Invalid relative path reference: ${{r!someFakePath}}",
        )

    def test_config_override_final(self):
        self.nmk("config_override_final.yml", expected_error="While loading {project}: Can't override final config BASEDIR")

    def test_config_builtin(self):
        self.nmk(
            "config_basedir_ref.yml",
            extra_args=[
                "--print",
                "ROOTDIR",
                "--print",
                "ROOTDIR_NMK",
                "--print",
                "CACHEDIR",
                "--print",
                "PROJECTDIR",
                "--print",
                "PROJECTDIR_NMK",
                "--print",
                "PROJECTFILES",
                "--print",
                "BASEDIR",
                "--print",
                "PACKAGESREFS",
                "--print",
                "foo",
            ],
        )

        # Check for patterns
        self.check_logs(
            "Config dump: { "
            + '"BASEDIR": "", '
            + f'"ROOTDIR": "{json_serialized_path(self.test_folder)}", '
            + f'"ROOTDIR_NMK": "{json_serialized_path(self.test_folder / ".nmk")}", '
            + f'"CACHEDIR": "{json_serialized_path(self.test_folder / ".nmk" / "cache")}", '
            + f'"PROJECTDIR": "{json_serialized_path(self.templates_root)}", '
            + f'"PROJECTDIR_NMK": "{json_serialized_path(self.templates_root / ".nmk")}", '
            + f'"PROJECTFILES": [ "{json_serialized_path(self.template("config_basedir_ref.yml"))}" ], '
            + '"PACKAGESREFS": [], '
            + f'"foo": "{json_serialized_path(self.templates_root)}/foo"'
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
        self.nmk("config_dot_ok.yml", extra_args=["--print", "tryDotRef", "--print", "someMap"])
        self.check_logs('Config dump: { "tryDotRef": "_bar_", "someMap": { "foo": "bar", "yo": 123 } }')

    def test_config_completion(self):
        # With final ones
        configs = ConfigCompleter()(
            "", None, None, NmkParser().parse(["--root", self.test_folder.as_posix(), "-p", self.template("config_sample.yml").as_posix()])
        )
        assert len(configs) == 6 + 9  # 6 provided one + 9 built-ins
        assert all(t in configs for t in ["someInt", "someString", "someBool", "someList", "someDict", "otherDict"])

        # Without final ones
        configs = ConfigCompleter(False)(
            "", None, None, NmkParser().parse(["--root", self.test_folder.as_posix(), "-p", self.template("config_sample.yml").as_posix()])
        )
        assert len(configs) == 6  # 6 provided one only (all built-ins are final)
        assert all(t in configs for t in ["someInt", "someString", "someBool", "someList", "someDict", "otherDict"])

    def test_config_escape(self):
        # Test escaping
        self.nmk("config_escape.yml", extra_args=["--print", "someString", "--print", "someOtherString", "--print", "someReferringStr"])
        self.check_logs(
            "Config dump: { "
            + '"someString": "${NotAnNmkConfigItem}", '
            + '"someOtherString": "some/path/${with}/escaped/${path}", '
            + '"someReferringStr": "__${NotAnNmkConfigItem}__"'
            + " }"
        )

    def test_config_inherit_type(self):
        # Test inheriting type
        self.nmk("config_inherit_type.yml", extra_args=["--print", "someBool"])
        self.check_logs('Config dump: { "someBool": true }')

        # Test inheriting type with override
        self.nmk("config_inherit_type_ref.yml", extra_args=["--print", "someBool"])
        self.check_logs('Config dump: { "someBool": false }')
