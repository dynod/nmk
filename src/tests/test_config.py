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
        self.nmk("unknown.yml", extra_args=["--config", '{"foo:'], expected_error="Invalid Json fragment for --config option: ")

    def test_config_invalid_json(self):
        self.nmk("unknown.yml", extra_args=["--config", '["foo"]'], expected_error="Json fragment for --config option must be an object")

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
            ],
        )
        self.check_logs(
            'Config dump: { "someString": "abcd", "someInt": 65, "someBool": false, "someList": [ "abc", "def" ], "someDict": { "adc": "def", "ghi": "jkl" } }'
        )

    def test_config_override_bad_type(self):
        self.nmk("config_sample.yml", extra_args=["--config", '{"someList":65}'], expected_error="Unexpected type change for config someList (list --> int)")

    def test_config_invalid_resolver(self):
        self.nmk("config_invalid_resolver.yml", expected_error="While loading {project}: Invalid resolver class qualified name: AbcDef (missing separator: .)")

    def test_config_unknown_module_resolver(self):
        self.nmk("config_unknown_resolver.yml", expected_error="While loading {project}: Can't instantiate resolver class foo.bar.SomeResolver:")

    def test_config_unknown_class_resolver(self):
        self.nmk(
            "config_unknown_class_resolver.yml",
            expected_error="While loading {project}: Can't instantiate resolver class tests.failling_resolvers.UnknownResolver: Can't find class UnknownResolver in module tests.failling_resolvers",
        )

    def test_config_exception_resolver(self):
        self.nmk(
            "config_exception_resolver.yml",
            expected_error="While loading {project}: Can't instantiate resolver class tests.failling_resolvers.FaillingResolver: Can't instantiate abstract class FaillingResolver",
        )

    def test_config_bad_type_resolver(self):
        self.nmk(
            "config_bad_type_resolver.yml",
            expected_error="While loading {project}: Unexpected type for loaded class tests.failling_resolvers.BadTypeResolver: got BadTypeResolver, expecting NmkConfigResolver subclass",
        )

    def test_config_str_resolver(self):
        self.nmk("config_str_resolver.yml", extra_args=["--print", "someResolved"])
        self.check_logs('Config dump: { "someResolved": "my dynamic value" }')

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
