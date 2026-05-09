"""
Business-logic layer.

Views stay thin and delegate here. Services are framework-agnostic
where possible — they accept Django models but contain no HTTP
concerns. This keeps testing and reuse simple.
"""
