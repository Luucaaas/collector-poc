{{- define "collector-service.name" -}}
{{- default .Release.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Image: always repository:tag@digest (pinning is mandatory). */}}
{{- define "collector-service.image" -}}
{{- $tag := required "image.tag is required (e.g. sha-bec38ed)" .Values.image.tag -}}
{{- $repo := required "image.repository is required" .Values.image.repository -}}
{{- $digest := required "image.digest is required (sha256:... of the index, provided by deploy.sh)" .Values.image.digest -}}
{{ $repo }}:{{ $tag }}@{{ $digest }}
{{- end -}}

{{- define "collector-service.labels" -}}
app.kubernetes.io/name: {{ include "collector-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "collector-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "collector-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* Security context shared by the application container and the migration Job. */}}
{{- define "collector-service.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
runAsNonRoot: true
runAsUser: {{ .Values.podSecurity.uid }}
runAsGroup: {{ .Values.podSecurity.gid }}
capabilities:
  drop: ["ALL"]
seccompProfile:
  type: RuntimeDefault
{{- end -}}
