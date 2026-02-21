*** Settings ***
Documentation     A test suite for error cases.

Resource  functional.resource

Suite Setup  Error Suite Setup
Suite Teardown  Custom Suite Teardown

Test Teardown    Custom Test Teardown    ${TEST NAME}


*** Test Cases ***

Make an HTTPS request with Custom CA on simple-https-server without restarting HomeAssistant
    [Documentation]  HomeAssistant should not be able to make an https request on a custom server without restarting HomeAssistant
    ${response} =  Run Keyword And Expect Error  HTTPError: 500 Server Error: Internal Server Error for url: http://localhost:8123/api/services/rest_command/additional_ca_test?return_response  Run HomeAssistant Action Rest Command    additional_ca_test
    HomeAssistant Logs Should Match Regex    CA 'simple-https-server.pem' with Common Name 'mkcert root@.*' is missing in SSL Context. Home Assistant needs to be restarted.
    HomeAssistant Logs Should Match Regex    Cannot connect to host simple-https-server:4433 ssl:True .SSLCertVerificationError: ..*, '.SSL: CERTIFICATE_VERIFY_FAILED. certificate verify failed: unable to get local issuer certificate ..*.'..
