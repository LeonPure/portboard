#!/usr/bin/env node

"use strict";

const { main } = require("../lib/launcher");

process.exitCode = main();
