*** Settings ***
Documentation     Resource file for integration tests

Library    Process
Library    RequestsLibrary
Library    OperatingSystem


*** Keywords ***

Normal Suite Setup
    Copy File    test/integration/files/configuration_no_force.yaml    test/integration/files/config/configuration.yaml
    Start HomeAssistant container    environment_var=REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    # HomeAssistant needs to be restarted to take new CAs into account
    Attempt to restart HomeAssistant


Error Suite Setup
    Copy File    test/integration/files/configuration_error_case.yaml    test/integration/files/config/configuration.yaml
    Start HomeAssistant container


Custom Suite Teardown
    Stop HomeAssistant container


Start HomeAssistant container
    [Arguments]    ${environment_var}=foo=bar
    @{docker_run_args} =  Create List
    ...  run
    ...  --rm
    ...  --name  homeassistant
    ...  --env  TZ=UTC
    ...  --env  PYTHONUNBUFFERED=1
    ...  --env  ${environment_var}
    ...  -v  ${GITHUB_WORKSPACE}/test/integration/files/config:/config
    ...  -p  8123:8123
    ...  -d
    ...  ghcr.io/home-assistant/home-assistant:stable
    ${result} =    Run Process    docker  @{docker_run_args}  stdout=stdout_docker_run2.txt  stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Log To Console  container ${result.stdout} created
    Wait Until Keyword Succeeds    120s    5s    Wait Until Additional CA integration is loaded
    RETURN    ${result.stdout}


Stop HomeAssistant container
    @{docker_run_args} =  Create List  stop  homeassistant
    ${result} =    Run Process    docker  @{docker_run_args}  stdout=stdout_docker_stop.txt  stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Wait Until Keyword Succeeds    30s    2s    Container Should Not Exist    homeassistant
    Log To Console  ${result.stdout} stopped
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
    Wait Until Additional CA integration is loaded
    RETURN  ${response}


Container Should Not Exist
    [Arguments]    ${container_name}
    @{docker_run_args} =  Create List
    ...    ps
    ...    -a
    ...    --filter    name=${container_name}
    ...    --format    {{.Names}}
    ${result} =    Run Process    docker    @{docker_run_args}    stdout=stdout_docker_ps.txt    stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Should Not Contain    ${result.stdout}    ${container_name}


HomeAssistant Logs Should Not Contain
    [Arguments]    ${string_to_check}
    ${log_content} =    Get File    test/integration/files/config/home-assistant.log
    Should Not Contain    ${log_content}    ${string_to_check}    msg=HomeAssistant logs contain the unexpected string: '${string_to_check}'    values=False


HomeAssistant Logs Should Contain
    [Arguments]    ${string_to_check}
    ${log_content} =    Get File    test/integration/files/config/home-assistant.log
    Should Contain    ${log_content}    ${string_to_check}    msg=HomeAssistant logs do not contain the expected string: '${string_to_check}'    values=False
