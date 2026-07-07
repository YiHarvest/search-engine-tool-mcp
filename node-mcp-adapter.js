const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  InitializeRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const fs = require('fs');
const path = require('path');

// 记录到文件，保持 stderr 用于 MCP 协议通信
const debugLog = (msg) => {
  try {
    fs.appendFileSync(path.join(__dirname, 'mcp-debug.log'), `[${new Date().toISOString()}] ${msg}\n`);
  } catch (e) {
    // 忽略日志文件写入错误
  }
};

const CONFIG_PATH = path.join(__dirname, 'mcp-tools.config.json');

let loadedModules = {};
let toolConfigs = {};

function loadConfig() {
  try {
    const configData = fs.readFileSync(CONFIG_PATH, 'utf8');
    const config = JSON.parse(configData);
    return config.tools || [];
  } catch (error) {
    debugLog(`Failed to load config from ${CONFIG_PATH}: ${error.message}`);
    return [];
  }
}

function loadModule(modulePath, exportType, functionName) {
  const cacheKey = `${modulePath}:${exportType}:${functionName}`;
  
  if (loadedModules[cacheKey]) {
    return loadedModules[cacheKey];
  }

  try {
    const fullPath = path.resolve(__dirname, modulePath);
    const moduleExports = require(fullPath);
    
    let targetFunction;
    
    if (exportType === 'default') {
      targetFunction = moduleExports;
    } else if (exportType === 'named') {
      if (functionName) {
        targetFunction = moduleExports[functionName];
      } else {
        throw new Error(`functionName is required for named export type`);
      }
    } else {
      throw new Error(`Unknown export type: ${exportType}`);
    }

    if (typeof targetFunction !== 'function') {
      throw new Error(`Target is not a function. Type: ${typeof targetFunction}`);
    }

    loadedModules[cacheKey] = targetFunction;
    return targetFunction;
  } catch (error) {
    debugLog(`Failed to load module ${modulePath}: ${error.message}`);
    throw error;
  }
}

function mapParameters(inputParams, parameterMapping) {
  const targetParams = {};
  
  if (parameterMapping && parameterMapping.targetFunction) {
    const mapping = parameterMapping.targetFunction;
    
    for (const [targetKey, sourceKey] of Object.entries(mapping)) {
      if (inputParams[sourceKey] !== undefined) {
        targetParams[targetKey] = inputParams[sourceKey];
      }
    }
  } else {
    Object.assign(targetParams, inputParams);
  }
  
  return targetParams;
}

function formatResult(rawResult, formattingConfig, inputParams) {
  if (!formattingConfig) {
    return rawResult;
  }

  if (formattingConfig.type === 'wrapper') {
    const template = formattingConfig.template || {};
    
    let processedResults = rawResult;
    
    if (formattingConfig.sliceLimit && inputParams[formattingConfig.sliceLimit]) {
      const limit = inputParams[formattingConfig.sliceLimit];
      if (Array.isArray(rawResult)) {
        processedResults = rawResult.slice(0, limit);
      }
    }
    
    return {
      query: inputParams.query || '',
      engine: inputParams.engine || 'default',
      limit: inputParams.limit || 0,
      count: Array.isArray(processedResults) ? processedResults.length : 0,
      results: processedResults
    };
  }

  if (formattingConfig.type === 'passthrough') {
    return rawResult;
  }

  return rawResult;
}

async function executeTool(toolConfig, args) {
  try {
    const targetFunction = loadModule(
      toolConfig.modulePath,
      toolConfig.exportType || 'default',
      toolConfig.functionName
    );

    const mappedParams = mapParameters(args, toolConfig.parameterMapping);
    
    debugLog(`Executing tool ${toolConfig.name} with params: ${JSON.stringify(mappedParams)}`);
    
    let orderedArgs;
    if (toolConfig.argumentOrder && Array.isArray(toolConfig.argumentOrder)) {
      orderedArgs = toolConfig.argumentOrder.map(key => mappedParams[key]);
    } else {
      orderedArgs = Object.values(mappedParams);
    }
    
    let rawResult;
    if (targetFunction.constructor.name === 'AsyncFunction') {
      rawResult = await targetFunction(...orderedArgs);
    } else {
      rawResult = targetFunction(...orderedArgs);
    }
    
    const formattedResult = formatResult(rawResult, toolConfig.resultFormatting, args);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(formattedResult, null, 2)
        }
      ]
    };
  } catch (error) {
    debugLog(`Error executing tool ${toolConfig.name}: ${error.message}`);
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            error: error.message,
            tool: toolConfig.name
          }, null, 2)
        }
      ],
      isError: true
    };
  }
}

async function main() {
  debugLog('Starting Node MCP Adapter...');

  const toolConfigsList = loadConfig();
  
  if (toolConfigsList.length === 0) {
    debugLog('No tools configured. Exiting.');
    process.exit(1);
  }

  toolConfigsList.forEach(config => {
    toolConfigs[config.name] = config;
    debugLog(`Loaded tool configuration: ${config.name}`);
  });

  const server = new Server(
    {
      name: 'node-mcp-adapter',
      version: '1.0.0'
    },
    {
      capabilities: {
        tools: {}
      }
    }
  );

  // 处理 initialize 请求
  server.setRequestHandler(InitializeRequestSchema, async (request) => {
    debugLog('Received initialize request');
    return {
      protocolVersion: '2024-11-05',
      capabilities: {
        tools: {}
      },
      serverInfo: {
        name: 'node-mcp-adapter',
        version: '1.0.0'
      }
    };
  });

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    const tools = Object.values(toolConfigs).map(config => ({
      name: config.name,
      description: config.description,
      inputSchema: config.inputSchema
    }));
    
  debugLog(`Listing ${tools.length} tools`);
    return { tools };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    
    debugLog(`Tool called: ${name} with args: ${JSON.stringify(args)}`);
    
    const toolConfig = toolConfigs[name];
    
    if (!toolConfig) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              error: `Tool not found: ${name}`
            }, null, 2)
          }
        ],
        isError: true
      };
    }
    
    return await executeTool(toolConfig, args);
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  debugLog('Node MCP Adapter started successfully');
}

main().catch((error) => {
  debugLog(`Fatal error in main(): ${error.message}`);
  process.exit(1);
});