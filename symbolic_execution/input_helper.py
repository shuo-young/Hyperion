import logging
import os
import re
import subprocess

import six


class InputHelper:
    def __init__(self, **kwargs):
        attr_defaults = {
            'source': None,
            'evm': False,
        }

        for attr, default in six.iteritems(attr_defaults):
            val = kwargs.get(attr, default)
            if val == None:
                raise Exception("'%s' attribute can't be None" % attr)
            else:
                setattr(self, attr, val)

    def get_inputs(self, targetContracts=None):
        inputs = []

        with open(self.source, 'r') as f:
            bytecode = f.read()
        self._prepare_disasm_file(self.source, bytecode)

        disasm_file = self._get_temporary_files(self.source)['disasm']
        inputs.append({'disasm_file': disasm_file})

        if targetContracts is not None and not inputs:
            raise ValueError("Targeted contracts weren't found in the source code!")
        return inputs

    def rm_tmp_files(self):
        self._rm_tmp_files(self.source)

    def _removeSwarmHash(self, evm):
        evm_without_hash = re.sub(r"a165627a7a72305820\S{64}0029$", "", evm)
        return evm_without_hash

    def _prepare_disasm_file(self, target, bytecode):
        self._write_evm_file(target, bytecode)
        self._write_disasm_file(target)

    def _get_temporary_files(self, target):
        return {
            "evm": target + ".evm",
            "disasm": target + ".evm.disasm",
            "log": target + ".evm.disasm.log",
        }

    def _write_evm_file(self, target, bytecode):
        evm_file = self._get_temporary_files(target)["evm"]
        with open(evm_file, "w") as of:
            of.write(self._removeSwarmHash(bytecode))

    def _write_disasm_file(self, target):
        tmp_files = self._get_temporary_files(target)
        evm_file = tmp_files["evm"]
        disasm_file = tmp_files["disasm"]
        disasm_out = ""
        try:
            disasm_p = subprocess.Popen(
                ["evm", "disasm", evm_file], stdout=subprocess.PIPE
            )
            disasm_out = disasm_p.communicate()[0].decode("utf-8", "strict")
        except:
            logging.critical("Disassembly failed.")
            exit()

        with open(disasm_file, "w") as of:
            of.write(disasm_out)

    def _rm_tmp_files(self, target):
        tmp_files = self._get_temporary_files(target)
        if not self.evm:
            self._rm_file(tmp_files["evm"])
            self._rm_file(tmp_files["disasm"])
        self._rm_file(tmp_files["log"])

    def _rm_file(self, path):
        if os.path.isfile(path):
            os.unlink(path)
