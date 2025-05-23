# Synonym dictionary for query expansion in Augmentorium
# Expanded to include terms from many programming languages, frameworks, and domains

SYNONYM_DICT = {
    # General programming
    "function": ["method", "routine", "procedure", "lambda", "arrow function", "callback", "fun", "subroutine"],
    "functions": ["methods", "routines", "procedures", "lambdas", "arrow functions", "callbacks", "subs"],
    "method": ["function", "routine", "procedure", "member function"],
    "procedure": ["function", "routine", "method", "subroutine"],
    "subroutine": ["procedure", "function", "routine"],
    "lambda": ["anonymous function", "arrow function", "closure"],
    "arrow function": ["lambda", "anonymous function"],
    "callback": ["handler", "listener", "function"],
    "constructor": ["initializer", "ctor", "init"],
    "destructor": ["finalizer", "dtor", "cleanup"],
    "variable": ["parameter", "argument", "field", "property", "attribute", "var", "let", "const", "symbol"],
    "variables": ["parameters", "arguments", "fields", "properties", "attributes", "vars", "lets", "consts", "symbols"],
    "parameter": ["argument", "variable", "input"],
    "parameters": ["arguments", "variables", "inputs"],
    "argument": ["parameter", "variable", "input"],
    "arguments": ["parameters", "variables", "inputs"],
    "field": ["property", "attribute", "column", "member"],
    "property": ["field", "attribute", "member"],
    "attribute": ["field", "property", "decorator"],
    "constant": ["const", "final", "static", "literal"],
    "const": ["constant", "final", "static", "literal"],
    "enum": ["enumeration", "symbol set"],
    "class": ["type", "object", "constructor", "prototype", "struct", "record"],
    "classes": ["types", "objects", "constructors", "prototypes", "structs", "records"],
    "object": ["instance", "entity", "record", "struct", "map", "hash"],
    "objects": ["instances", "entities", "records", "structs", "maps", "hashes"],
    "struct": ["structure", "record", "object"],
    "record": ["struct", "object", "row", "tuple"],
    "interface": ["protocol", "contract", "trait", "api"],
    "trait": ["interface", "mixin"],
    "mixin": ["trait", "extension"],
    "module": ["package", "namespace", "library", "crate", "gem", "bundle"],
    "package": ["module", "library", "namespace", "crate", "gem", "bundle"],
    "namespace": ["module", "package", "scope"],
    "library": ["module", "package", "framework"],
    "framework": ["library", "platform", "toolkit"],
    "crate": ["package", "module", "library"],
    "gem": ["package", "module", "library"],
    "bundle": ["package", "module", "library"],
    "script": ["program", "code", "file", "shell script", "batch file"],
    "program": ["application", "script", "software", "executable"],
    "application": ["app", "program", "software"],
    "statement": ["expression", "command", "instruction", "line"],
    "expression": ["statement", "formula", "lambda", "expr"],
    "command": ["statement", "instruction", "cli"],
    "instruction": ["statement", "command"],
    "loop": ["iteration", "for", "while", "repeat", "foreach", "do-while"],
    "iteration": ["loop", "cycle", "pass"],
    "recursion": ["recursive", "loop"],
    "array": ["list", "vector", "sequence", "slice", "collection"],
    "list": ["array", "vector", "sequence", "collection"],
    "vector": ["array", "list", "sequence"],
    "slice": ["array", "list", "vector"],
    "map": ["dictionary", "object", "hash", "table", "associative array"],
    "dictionary": ["map", "hash", "object", "table", "dict"],
    "hash": ["map", "dictionary", "object", "hashmap"],
    "set": ["collection", "group", "bag"],
    "queue": ["fifo", "buffer", "channel"],
    "stack": ["lifo", "buffer"],
    "pointer": ["reference", "address", "ptr"],
    "reference": ["pointer", "address", "ref"],
    "file": ["document", "script", "resource", "asset", "blob"],
    "files": ["documents", "scripts", "resources", "assets", "blobs"],
    "document": ["file", "doc", "text", "page", "record"],
    "documents": ["files", "docs", "texts", "pages", "records"],
    "text": ["string", "document", "content", "char array"],
    "string": ["text", "char array", "str"],
    "char": ["character", "byte"],
    "character": ["char", "byte"],
    "byte": ["octet", "character", "char"],
    "number": ["integer", "float", "double", "numeric", "decimal", "num"],
    "integer": ["int", "number", "whole number"],
    "float": ["double", "number", "real"],
    "double": ["float", "number", "real"],
    "boolean": ["bool", "flag", "truth value"],
    "bool": ["boolean", "flag", "truth value"],
    "null": ["none", "nil", "undefined", "void"],
    "undefined": ["null", "none", "nil", "void"],
    "none": ["null", "nil", "undefined", "void"],
    "nil": ["null", "none", "undefined", "void"],
    "void": ["null", "none", "nil", "undefined"],
    "true": ["yes", "on", "enabled", "1"],
    "false": ["no", "off", "disabled", "0"],

    # Web development
    "element": ["node", "component", "widget", "tag", "dom element"],
    "component": ["element", "widget", "module", "react component", "vue component", "angular component"],
    "widget": ["component", "element", "ui element"],
    "selector": ["query", "pattern", "css selector"],
    "event": ["signal", "trigger", "callback", "listener"],
    "handler": ["listener", "callback", "event handler"],
    "listener": ["handler", "callback", "event listener"],
    "attribute": ["property", "field", "html attribute"],
    "prop": ["property", "attribute"],
    "props": ["properties", "attributes"],
    "state": ["status", "condition"],
    "hook": ["callback", "function", "react hook"],
    "middleware": ["interceptor", "filter", "plugin"],

    # Databases
    "table": ["relation", "dataset", "spreadsheet"],
    "row": ["record", "entry", "tuple"],
    "column": ["field", "attribute"],
    "record": ["row", "entry", "object", "document"],
    "index": ["key", "pointer", "idx"],
    "key": ["index", "identifier", "primary key", "foreign key"],
    "value": ["data", "entry", "val"],
    "primary key": ["pk", "key"],
    "foreign key": ["fk", "key"],
    "schema": ["structure", "definition", "model"],
    "migration": ["update", "change", "alteration"],
    "query": ["search", "request", "lookup", "sql", "find"],

    # Networking / APIs
    "api": ["endpoint", "service", "interface", "rest api", "graphql api"],
    "endpoint": ["api", "route", "url", "path"],
    "request": ["call", "query", "http request"],
    "response": ["reply", "result", "http response"],
    "server": ["host", "backend", "service", "daemon"],
    "client": ["frontend", "consumer", "user agent"],
    "route": ["path", "endpoint", "url"],
    "url": ["uri", "link", "address"],
    "http": ["hypertext transfer protocol"],
    "websocket": ["ws", "socket", "connection"],
    "cors": ["cross-origin resource sharing"],

    # Build/DevOps/Cloud
    "build": ["compile", "make", "assemble", "build job"],
    "deploy": ["release", "publish", "ship", "deployment"],
    "pipeline": ["workflow", "process", "ci/cd"],
    "ci": ["continuous integration", "pipeline"],
    "cd": ["continuous deployment", "pipeline"],
    "job": ["task", "process", "build job"],
    "task": ["job", "process", "step"],
    "process": ["task", "job", "thread", "worker"],
    "thread": ["process", "worker", "fiber"],
    "container": ["docker", "pod", "image"],
    "pod": ["container", "kubernetes pod"],
    "cluster": ["group", "farm", "kubernetes cluster"],
    "node": ["server", "host", "instance", "worker"],
    "vm": ["virtual machine", "instance"],
    "region": ["zone", "area", "location"],
    "zone": ["region", "area", "location"],
    "service": ["api", "daemon", "microservice"],

    # Testing/QA
    "test": ["check", "verify", "assert", "spec"],
    "tests": ["checks", "verifications", "assertions", "specs"],
    "assert": ["check", "verify", "test", "expect"],
    "mock": ["stub", "fake", "dummy", "test double"],
    "stub": ["mock", "fake", "dummy", "test double"],
    "spy": ["mock", "test double", "observer"],
    "integration test": ["end-to-end test", "e2e test"],
    "unit test": ["component test", "module test"],
    "regression test": ["backward compatibility test"],
    "smoke test": ["sanity test"],
    "acceptance test": ["uat", "user acceptance test"],

    # Errors/Debugging
    "error": ["exception", "fault", "bug", "issue", "problem", "failure"],
    "errors": ["exceptions", "faults", "bugs", "issues", "problems", "failures"],
    "exception": ["error", "fault", "bug", "throwable"],
    "bug": ["error", "fault", "issue", "defect"],
    "fault": ["error", "bug", "defect", "failure"],
    "issue": ["bug", "ticket", "problem", "case"],
    "ticket": ["issue", "bug", "task", "case"],
    "log": ["record", "trace", "output", "logging"],
    "trace": ["log", "stacktrace", "backtrace", "traceback"],
    "stacktrace": ["trace", "backtrace", "traceback"],
    "debug": ["troubleshoot", "analyze", "inspect"],

    # Version control
    "commit": ["change", "revision", "check-in"],
    "branch": ["fork", "line", "feature branch"],
    "merge": ["combine", "integrate", "pull request"],
    "pull request": ["merge request", "pr", "mr"],
    "review": ["code review", "inspection", "peer review"],
    "refactor": ["restructure", "rewrite", "clean up"],
    "cherry-pick": ["selective merge"],

    # Security/Auth
    "auth": ["authentication", "authorization", "login", "oauth"],
    "login": ["sign in", "authenticate", "logon"],
    "logout": ["sign out", "deauthenticate", "logoff"],
    "session": ["connection", "context", "user session"],
    "cookie": ["token", "session", "http cookie"],
    "token": ["cookie", "key", "credential", "jwt"],
    "hash": ["digest", "checksum", "hashcode"],
    "encryption": ["cipher", "crypto", "cryptography"],
    "decryption": ["decipher", "decode", "decrypt"],
    "jwt": ["json web token", "token"],

    # Serialization/Data
    "serialize": ["marshal", "encode", "save", "dump"],
    "deserialize": ["unmarshal", "decode", "load", "parse"],
    "json": ["javascript object notation", "data format"],
    "xml": ["extensible markup language", "data format"],
    "yaml": ["yet another markup language", "data format"],
    "csv": ["comma separated values", "data format"],

    # Miscellaneous
    "search": ["find", "lookup", "query", "filter", "scan"],
    "query": ["search", "request", "lookup", "sql", "find"],
    "retrieve": ["fetch", "get", "obtain", "load", "pull"],
    "retrieves": ["fetches", "gets", "obtains", "loads", "pulls"],
    "chunk": ["segment", "piece", "block", "partition", "shard"],
    "chunks": ["segments", "pieces", "blocks", "partitions", "shards"],
    "project": ["repo", "repository", "workspace", "solution", "project folder"],
    "projects": ["repos", "repositories", "workspaces", "solutions", "project folders"],
    "optimize": ["improve", "tune", "refactor", "enhance"],
    "performance": ["speed", "efficiency", "throughput", "latency"],
    "scalability": ["scaling", "expandability", "elasticity"],
    "security": ["safety", "protection", "infosec"],
    "configuration": ["settings", "setup", "config", "preferences"],
    "settings": ["configuration", "preferences", "options"],
    "file": ["document", "resource", "asset", "blob"],
    "files": ["documents", "resources", "assets", "blobs"],
    "monitoring": ["observability", "metrics", "logging"],
    "logging": ["monitoring", "log", "trace"],
    "alert": ["notification", "alarm", "warning"],
    "dashboard": ["panel", "monitor", "ui"],
    "ui": ["user interface", "frontend", "gui"],
    "ux": ["user experience", "design"],
    "cli": ["command line", "terminal", "shell"],
    "shell": ["cli", "terminal", "command line"],
    "terminal": ["shell", "cli", "console"],
    "console": ["terminal", "shell", "cli"],
    "os": ["operating system", "platform"],
    "platform": ["os", "system"],
    "thread": ["fiber", "process", "worker"],
    "worker": ["thread", "process", "job"],
    "job": ["worker", "task", "process"],
    "pipeline": ["workflow", "ci/cd", "process"],
    "workflow": ["pipeline", "process", "automation"],
    "automation": ["workflow", "scripting", "robotics"],
    "robot": ["bot", "automation", "agent"],
    "agent": ["robot", "bot", "automation"],
    "ml": ["machine learning", "ai", "artificial intelligence"],
    "ai": ["artificial intelligence", "ml", "machine learning"],
    "data": ["dataset", "information", "record"],
    "dataset": ["data", "corpus", "collection"],
    "corpus": ["dataset", "data", "collection"],
    "etl": ["extract transform load", "data pipeline"],
    "migration": ["update", "change", "alteration", "schema migration"],
    "schema": ["structure", "definition", "model", "blueprint"],
    "model": ["schema", "blueprint", "representation"],
    "view": ["page", "screen", "ui"],
    "controller": ["handler", "manager", "coordinator"],
    "manager": ["controller", "handler", "coordinator"],
    "coordinator": ["manager", "controller", "handler"],
    "service": ["api", "daemon", "microservice", "backend"],
    "daemon": ["service", "background process"],
    "microservice": ["service", "api", "component"],
    "backend": ["server", "api", "service"],
    "frontend": ["client", "ui", "user interface"],
    "user": ["client", "customer", "end user"],
    "customer": ["user", "client", "end user"],
    "end user": ["user", "customer", "client"],
    "admin": ["administrator", "superuser", "root"],
    "administrator": ["admin", "superuser", "root"],
    "superuser": ["admin", "administrator", "root"],
    "root": ["admin", "administrator", "superuser"],
    "owner": ["admin", "user", "creator"],
    "creator": ["owner", "author", "maker"],
    "author": ["creator", "owner", "writer"],
    "writer": ["author", "creator", "owner"],
}