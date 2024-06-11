#!/bin/bash

if [ -z "$SERVICE_NAME" ]; then
    echo "SERVICE_NAME is not set"
    exit 1
fi

wait_for_service_state(){
    STATES=( "$@" )
    echo "Waiting for service '$SERVICE_NAME' to be in any of these states: ${STATES[@]}"
    while true; do
        sleep ${SLEEP_INTERVAL:-10}
        SERVICE_OBJ=$(aws lightsail get-container-services --service-name "$SERVICE_NAME")
        local SVC_STATE=$(echo "$SERVICE_OBJ" | jq -r '.containerServices[0].state')
        echo "- service state: $SVC_STATE"
        for STATE in "${STATES[@]}"; do
            # echo "Checking state: $STATE"
            if [ "$SVC_STATE" == "$STATE" ]; then
                echo "Service $SERVICE_NAME is in state: $SVC_STATE"
                return
            fi
        done
    done
}

wait_for_next_container(){
    echo "Waiting for deployment $TARGET_DEP_VERSION to be Active"
    while true; do
        sleep 30
        local SERVICE_OBJ=$(aws lightsail get-container-services --service-name "$SERVICE_NAME")
        local SVC_STATE=$(echo "$SERVICE_OBJ" | jq -r '.containerServices[0].state')
        local CURR_DEP_VER=$(echo "$SERVICE_OBJ" | jq -r '.containerServices[0].currentDeployment.version')
        local NEXT_DEP_VER=$(echo "$SERVICE_OBJ" | jq -r '.containerServices[0].nextDeployment.version')
        echo "- Service $SVC_STATE: current deployment $CURR_DEP_VER; next deployment $NEXT_DEP_VER"
        if [ "$NEXT_DEP_VER" == "null" ]; then
            local LAST_DEPLOYMENT_STATE=$(aws lightsail get-container-service-deployments --service-name "$SERVICE_NAME" | jq -r ".deployments[] | select(.version == $TARGET_DEP_VERSION) | .state")
            if [ "$LAST_DEPLOYMENT_STATE" == "FAILED" ]; then
                echo "Deployment $TARGET_DEP_VERSION failed! Increase the power of the service or check logs at https://lightsail.aws.amazon.com/ls/webapp/us-east-1/container-services/$SERVICE_NAME/deployments"
                return 99
            elif [ "$LAST_DEPLOYMENT_STATE" == "ACTIVE" ]; then
                echo "Deployment $TARGET_DEP_VERSION is Active"
                return
            else
                echo "Unhandled deployment state: '$LAST_DEPLOYMENT_STATE'"
                return 91
            fi
        fi
    done
}

case "$1" in
    deployment)
        SLEEP_INTERVAL=5 wait_for_service_state DEPLOYING
        TARGET_DEP_VERSION=$(echo "$SERVICE_OBJ" | jq -r '.containerServices[0].nextDeployment.version')
        wait_for_next_container
        ;;
    service)
        shift
        wait_for_service_state "$@"
        ;;
esac

