*** Settings ***
Documentation     Resource file for integration tests

Library    Process
Library   RequestsLibrary


*** Keywords ***

Normal Suite Setup
    Start HomeAssistant container with REQUESTS_CA_BUNDLE env var
    # HomeAssistant needs to be restarted to take new CAs into account
    Attempt to restart HomeAssistant


Error Suite Setup
    Start HomeAssistant container


Custom Suite Teardown
    Stop HomeAssistant container


Start HomeAssistant container with REQUESTS_CA_BUNDLE env var
    @{docker_run_args} =  Create List
    ...  run
    ...  --rm
    ...  --name  homeassistant
    ...  --env  TZ=UTC
    ...  --env  PYTHONUNBUFFERED=1
    ...  --env  REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    ...  -v  ${GITHUB_WORKSPACE}/test/integration/files/config:/config
    ...  -p  8123:8123
    ...  -d
    ...  ghcr.io/home-assistant/home-assistant:stable
    ${result} =    Run Process    docker  @{docker_run_args}  stdout=stdout.txt  stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Log To Console  ${result.stdout}
    Wait Until Keyword Succeeds    120s    5s    Wait Until Additional CA integration is loaded
    RETURN    ${result.stdout}


Start HomeAssistant container
    @{docker_run_args} =  Create List
    ...  run
    ...  --rm
    ...  --name  homeassistant
    ...  --env  TZ=UTC
    ...  --env  PYTHONUNBUFFERED=1
    ...  -v  ${GITHUB_WORKSPACE}/test/integration/files/config:/config
    ...  -p  8123:8123
    ...  -d
    ...  ghcr.io/home-assistant/home-assistant:stable
    ${result} =    Run Process    docker  @{docker_run_args}  stdout=stdout.txt  stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Log To Console  ${result.stdout}
    Wait Until Keyword Succeeds    120s    5s    Wait Until Additional CA integration is loaded
    RETURN    ${result.stdout}


Stop HomeAssistant container
    @{docker_run_args} =  Create List  stop  homeassistant
    ${result} =    Run Process    docker  @{docker_run_args}  stdout=stdout.txt  stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    # Log To Console  ${result.stderr}
    Log To Console  ${result.stdout}
    RETURN    ${result.stdout}


Wait Until Additional CA integration is loaded
    ${headers}  Create Dictionary
    ...    Authorization=Bearer ${HASS_TOKEN}
    ...    Content-Type=application/json
    ${response} =  Wait Until Keyword Succeeds    120s    5s    GET  http://localhost:8123/api/config/config_entries/entry
    ...    headers=${headers}

    # Check if additional_ca domain is loaded
    ${additional_ca_found} =  Set Variable  ${False}
    FOR  ${entry}  IN  @{response.json()}
        IF  '${entry["domain"]}' == 'additional_ca' and '${entry["state"]}' == 'loaded'
            ${additional_ca_found} =  Set Variable  ${True}
            Log To Console  Additional CA integration found and loaded
            BREAK
        END
    END
    Should Be True  ${additional_ca_found}  msg=Additional CA integration not found or not loaded


Run HomeAssistant Action Rest Command
    [Arguments]    ${command_name}
    ${headers}  Create Dictionary
    ...    Authorization=Bearer ${HASS_TOKEN}
    ...    Content-Type=application/json
    ${response} =    POST  http://localhost:8123/api/services/rest_command/${command_name}
    ...  params=return_response
    ...  headers=${headers}
    RETURN  ${response}


Attempt to restart HomeAssistant
    ${headers}  Create Dictionary
    ...    Authorization=Bearer ${HASS_TOKEN}
    ...    Content-Type=application/json
    ${response} =    Wait Until Keyword Succeeds    120s    5s    POST  http://localhost:8123/api/services/homeassistant/restart
    ...  headers=${headers}
    RETURN  ${response}
