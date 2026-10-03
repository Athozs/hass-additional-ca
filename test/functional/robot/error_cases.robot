*** Settings ***
Documentation     A test suite for error cases.

Resource  functional.resource

Suite Setup  Error Suite Setup
Suite Teardown  Custom Suite Teardown

Test Teardown    Custom Test Teardown    ${TEST NAME}


*** Test Cases ***

Make an HTTPS request with Custom CA on simple-https-server without restarting HomeAssistant
    [Documentation]  HomeAssistant should be able to make an https request on a custom server without restarting HomeAssistant
    ${response} =  Wait Until Keyword Succeeds    60s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    HomeAssistant Logs Should Match Regex    SSL Context contains CA 'simple-https-server.pem' with Common Name 'mkcert root@.*'.
    HomeAssistant Logs Should Not Contain    is missing in SSL Context
