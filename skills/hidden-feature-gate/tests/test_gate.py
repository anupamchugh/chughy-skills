"""Behaviour tests for gate.py. Run: python3 -m unittest discover -s skills/hidden-feature-gate/tests"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

GATE = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'gate.py')


def run_gate(*args):
    return subprocess.run([sys.executable, GATE, *args], capture_output=True, text=True)


class SourceScan(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, rel, text):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as fh:
            fh.write(text)

    def test_launch_argument_outside_debug_fails(self):
        self.write('App/Launch.swift', 'let demo = ProcessInfo.processInfo.arguments.contains("-demo")\n')
        result = run_gate('--source', self.root)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Launch.swift:1', result.stdout)

    def test_switch_inside_debug_passes(self):
        self.write('App/Launch.swift', '#if DEBUG\nlet demo = ProcessInfo.processInfo.arguments.contains("-demo")\n#endif\n')
        result = run_gate('--source', self.root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_else_branch_of_debug_is_release_code(self):
        self.write('App/Launch.swift', '#if DEBUG\nlet a = 1\n#else\nlet mockPurchase = "MockPurchase"\n#endif\n')
        result = run_gate('--source', self.root)
        self.assertEqual(result.returncode, 1)

    def test_tests_folder_is_skipped(self):
        self.write('Tests/AppTests/MockStore.swift', 'let mock = MockStore()\nlet e = ProcessInfo.processInfo.environment\n')
        result = run_gate('--source', self.root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_demon_is_not_demo(self):
        self.write('App/Roles.swift', 'let role = "Demon"\nlet roles = ["Demon", "Imp"]\n')
        result = run_gate('--source', self.root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_no_arguments_is_a_usage_error(self):
        self.assertEqual(run_gate().returncode, 2)


@unittest.skipUnless(shutil.which('cc') and shutil.which('strings'), 'needs cc and strings')
class BinaryScan(unittest.TestCase):
    def build(self, text):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        src = os.path.join(root, 'main.c')
        exe = os.path.join(root, 'app')
        with open(src, 'w') as fh:
            fh.write('#include <stdio.h>\nint main(void){ puts("%s"); return 0; }\n' % text)
        subprocess.run(['cc', src, '-o', exe], check=True)
        return exe

    def test_launch_flag_in_binary_fails(self):
        result = run_gate('--binary', self.build('-openDemoMode'))
        self.assertEqual(result.returncode, 1)
        self.assertIn('-openDemoMode', result.stdout)

    def test_localhost_url_in_binary_fails(self):
        result = run_gate('--binary', self.build('http://127.0.0.1:8080/api'))
        self.assertEqual(result.returncode, 1)

    def test_clean_binary_passes(self):
        result = run_gate('--binary', self.build('Welcome to the town square'))
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main()
