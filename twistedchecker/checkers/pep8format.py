import sys
import StringIO
import re

from logilab import astng
from logilab.common.ureports import Table
from logilab.astng import are_exclusive

from pylint.interfaces import IASTNGChecker
from pylint.reporters import diff_string
from pylint.checkers import BaseChecker, EmptyReport

import pep8

class PEP8Checker(BaseChecker):
    """
    A checker for checking pep8 issues.
    Need pep8 installed.
    """
    msgs = {
     'W9010': ('Trailing whitespace found in the end of line',
               'Used when a line contains a trailing space.'),
     'W9011': ('Blank line contains whitespace',
               'Used when found a line contains whitespace.')
    }
    __implements__ = IASTNGChecker
    name = 'pep8'
    # map pep8 messages to messages in pylint.
    # it's foramt should look like this:
    # 'msgid in pep8' : ('msgid in pylint','a string to extract arguments')
    mapPEP8Messages = {
        'W291': ('W9010', ''),
        'W293': ('W9011', ''),
    }
    warnings = None
    pep8Checker = None


    def visit_module(self, node):
        """
        A interface will be called when visiting a module.
        """
        self._runPEP8Checker(node.file)


    def _recordErrors(self, lineNumber, offset, text, check):
        """
        A hack function to replace report_error in pep8.
        And record output warings.

        @param lineNumber: line number
        @param offset: column offset
        @param text: warning message
        @param check: check object in pep8
        """
        code = text[:4]
        self.warnings.append((self.pep8Checker.line_offset + lineNumber,
                              offset + 1, code, text))


    def _runPEP8Checker(self, file):
        """
        Call the checker of pep8

        @param file: path of module to check
        """
        pep8.options = pep8.process_options([file])[0]
        checker = pep8.Checker(file)
        checker.report_error = self._recordErrors
        # backup stdout
        stdoutBak = sys.stdout
        self.warnings = []
        self.pep8Checker = checker
        # set a stream to replace stdout, and get results in it
        streamResult = StringIO.StringIO()
        sys.stdout = streamResult
        checker.check_all()
        sys.stdout = stdoutBak
        self._outputMessages()


    def _outputMessages(self):
        """
        Map pep8 results to messages in pylint, then output them.
        """
        if not self.warnings:
            # no warnings were found
            return
        for warning in self.warnings:
            linenum, offset, msgidInPEP8, text = warning
            if msgidInPEP8 in self.mapPEP8Messages:
                msgid, patternArguments = self.mapPEP8Messages[msgidInPEP8]
                arguments = []
                if patternArguments:
                    matchResult = re.search(patternArguments, text)
                    if matchResult:
                        arguments = matchResult.groups()
                self.add_message(msgid, line=linenum, args=arguments)
