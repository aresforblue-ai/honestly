/**
 * Artillery processor for custom metrics
 */
module.exports = {
  // Custom metrics can be added here
  beforeRequest: (requestParams, context, ee, next) => {
    context.startTime = Date.now();
    return next();
  },
  
  afterResponse: (requestParams, response, context, ee, next) => {
    const duration = Date.now() - context.startTime;
    
    // Track response times
    if (!context.stats) {
      context.stats = { durations: [] };
    }
    context.stats.durations.push(duration);
    
    // Check if target met
    if (duration > 200) {
      console.warn(`Slow response: ${duration}ms for ${requestParams.url}`);
    }
    
    return next();
  },
};


