import shutil

from nmk.model.builder import NmkTaskBuilder


class SampleBuilder(NmkTaskBuilder):
    def build(self):
        assert len(self.task.outputs) > 0
        my_output = self.main_output
        if not my_output.is_file():
            self.logger.debug(f"Ready to write some input to {my_output}")
            with my_output.open("w") as f:
                f.write("bla bla bla")
        else:
            self.logger.debug(f"{my_output} already exists")


class CopyBuilder(NmkTaskBuilder):
    def build(self):
        f_input = self.main_input
        f_output = self.main_output
        self.logger.debug(f"Copying {f_input} to {f_output}")
        shutil.copyfile(f_input, f_output)


class ErrorBuilder(NmkTaskBuilder):
    def build(self):
        raise Exception("Some error happened!")


class ParamBuilder(NmkTaskBuilder):
    def build(self, foo: str, bar: int, ref: str):
        # Log param values
        self.logger.debug(f"foo:{foo} bar:{bar} ref:{ref}")


class CountInputsBuilder(NmkTaskBuilder):
    def build(self):
        # Count inputs!
        self.logger.warning(f"Inputs count: {len(self.inputs)}")
