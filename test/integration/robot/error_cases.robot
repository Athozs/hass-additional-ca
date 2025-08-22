*** Settings ***
Documentation     A test suite for error cases.

Resource  integration.resource

Suite Setup  Error Suite Setup
Suite Teardown  Custom Suite Teardown


*** Test Cases ***

Make an HTTPS request with Custom CA on self-signed.badssl.com without HomeAssistant restart
    ${response} =  Run Keyword And Expect Error  HTTPError: 500 Server Error: Internal Server Error for url: http://localhost:8123/api/services/rest_command/additional_ca_test?return_response  Run HomeAssistant Action Rest Command    additional_ca_test
    # TODO: add some checks of homeassistant.log
