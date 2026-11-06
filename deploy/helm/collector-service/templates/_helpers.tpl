{{- define "collector-service.name" -}}
{{- default .Release.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Image : toujours repository:tag@digest (épinglage obligatoire). */}}
{{- define "collector-service.image" -}}
{{- $tag := required "image.tag est obligatoire (ex. sha-bec38ed)" .Values.image.tag -}}
{{- $repo := required "image.repository est obligatoire" .Values.image.repository -}}
{{- $digest := required "image.digest est obligatoire (sha256:... de l'index, fourni par deploy.sh)" .Values.image.digest -}}
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

{{/* Contexte de sécurité commun au conteneur de l'application et au Job de migration. */}}
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
