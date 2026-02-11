const Vue = window.Vue;
Vue.compile;
Vue.Transition;
Vue.TransitionGroup;
Vue.VueElement;
Vue.createApp;
Vue.createSSRApp;
Vue.defineCustomElement;
Vue.defineSSRCustomElement;
Vue.hydrate;
Vue.initDirectivesForSSR;
Vue.nodeOps;
Vue.patchProp;
Vue.render;
Vue.useCssModule;
Vue.useCssVars;
Vue.useHost;
Vue.useShadowRoot;
Vue.vModelCheckbox;
Vue.vModelDynamic;
Vue.vModelRadio;
Vue.vModelSelect;
Vue.vModelText;
Vue.vShow;
Vue.withKeys;
Vue.withModifiers;
Vue.EffectScope;
Vue.ReactiveEffect;
Vue.TrackOpTypes;
Vue.TriggerOpTypes;
Vue.customRef;
Vue.effect;
Vue.effectScope;
Vue.getCurrentScope;
Vue.getCurrentWatcher;
Vue.isProxy;
Vue.isReactive;
Vue.isReadonly;
Vue.isRef;
Vue.isShallow;
Vue.markRaw;
Vue.onScopeDispose;
Vue.onWatcherCleanup;
Vue.proxyRefs;
Vue.reactive;
Vue.readonly;
const ref = Vue.ref;
Vue.shallowReactive;
Vue.shallowReadonly;
Vue.shallowRef;
Vue.stop;
Vue.toRaw;
Vue.toRef;
Vue.toRefs;
Vue.toValue;
Vue.triggerRef;
Vue.unref;
Vue.camelize;
Vue.capitalize;
Vue.normalizeClass;
Vue.normalizeProps;
Vue.normalizeStyle;
const toDisplayString = Vue.toDisplayString;
Vue.toHandlerKey;
Vue.BaseTransition;
Vue.BaseTransitionPropsValidators;
Vue.Comment;
Vue.DeprecationTypes;
Vue.ErrorCodes;
Vue.ErrorTypeStrings;
Vue.Fragment;
Vue.KeepAlive;
Vue.Static;
Vue.Suspense;
Vue.Teleport;
Vue.Text;
Vue.assertNumber;
Vue.callWithAsyncErrorHandling;
Vue.callWithErrorHandling;
Vue.cloneVNode;
Vue.compatUtils;
const computed = Vue.computed;
const createBlock = Vue.createBlock;
Vue.createCommentVNode;
Vue.createElementBlock;
const createElementVNode = Vue.createElementVNode;
Vue.createHydrationRenderer;
Vue.createPropsRestProxy;
Vue.createRenderer;
Vue.createSlots;
Vue.createStaticVNode;
Vue.createTextVNode;
Vue.createVNode;
Vue.defineAsyncComponent;
const defineComponent = Vue.defineComponent;
Vue.defineEmits;
Vue.defineExpose;
Vue.defineModel;
Vue.defineOptions;
Vue.defineProps;
Vue.defineSlots;
Vue.devtools;
Vue.getCurrentInstance;
Vue.getTransitionRawChildren;
Vue.guardReactiveProps;
Vue.h;
Vue.handleError;
Vue.hasInjectionContext;
Vue.hydrateOnIdle;
Vue.hydrateOnInteraction;
Vue.hydrateOnMediaQuery;
Vue.hydrateOnVisible;
Vue.initCustomFormatter;
Vue.inject;
Vue.isMemoSame;
Vue.isRuntimeOnly;
Vue.isVNode;
Vue.mergeDefaults;
Vue.mergeModels;
const mergeProps = Vue.mergeProps;
Vue.nextTick;
Vue.onActivated;
Vue.onBeforeMount;
Vue.onBeforeUnmount;
Vue.onBeforeUpdate;
Vue.onDeactivated;
Vue.onErrorCaptured;
Vue.onMounted;
Vue.onRenderTracked;
Vue.onRenderTriggered;
Vue.onServerPrefetch;
Vue.onUnmounted;
Vue.onUpdated;
const openBlock = Vue.openBlock;
Vue.popScopeId;
Vue.provide;
Vue.pushScopeId;
Vue.queuePostFlushCb;
Vue.registerRuntimeCompiler;
Vue.renderList;
Vue.renderSlot;
const resolveComponent = Vue.resolveComponent;
Vue.resolveDirective;
Vue.resolveDynamicComponent;
Vue.resolveFilter;
Vue.resolveTransitionHooks;
Vue.setBlockTracking;
Vue.setDevtoolsHook;
Vue.setTransitionHooks;
Vue.ssrContextKey;
Vue.ssrUtils;
Vue.toHandlers;
Vue.transformVNodeArgs;
Vue.useAttrs;
Vue.useId;
Vue.useModel;
Vue.useSSRContext;
Vue.useSlots;
Vue.useTemplateRef;
Vue.useTransitionState;
Vue.version;
Vue.warn;
Vue.watch;
Vue.watchEffect;
Vue.watchPostEffect;
Vue.watchSyncEffect;
Vue.withAsyncContext;
const withCtx = Vue.withCtx;
Vue.withDefaults;
Vue.withDirectives;
Vue.withMemo;
Vue.withScopeId;
const _hoisted_1 = { class: "ml-1" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "UploadButton",
  props: {
    icon: {},
    color: {},
    text: {},
    url: {}
  },
  setup(__props) {
    const props = __props;
    const filePickerRef = ref(null);
    const displayText = computed(
      () => props.text && props.text.length > 0 ? props.text : "Click Me"
    );
    const buttonProps = computed(() => {
      let propsCopy = { ...props };
      delete propsCopy.text;
      if (propsCopy.icon == null) delete propsCopy.icon;
      return propsCopy;
    });
    const handleButtonClick = () => filePickerRef.value?.click();
    const handleFilePickerChange = (event) => {
      const target = event.target;
      if (target.type !== "file") return;
      if (target.files == null || target.files.length === 0 || target.files.length > 1)
        return;
      const formData = new FormData();
      formData.append("file", target.files[0]);
      (async () => {
        try {
          const response = await fetch(props.url, {
            method: "POST",
            body: formData
          });
          const respData = await response.json();
          if (response.status !== 200) throw respData;
          window.location.href = respData.href;
        } catch (err) {
          console.error(err);
        }
      })();
    };
    return (_ctx, _cache) => {
      const _component_q_btn = resolveComponent("q-btn");
      return openBlock(), createBlock(_component_q_btn, mergeProps(buttonProps.value, { onClick: handleButtonClick }), {
        default: withCtx(() => [
          createElementVNode("span", _hoisted_1, toDisplayString(displayText.value), 1),
          createElementVNode("input", {
            type: "file",
            ref_key: "filePickerRef",
            ref: filePickerRef,
            class: "hidden",
            onChange: handleFilePickerChange
          }, null, 544)
        ]),
        _: 1
      }, 16);
    };
  }
});
export {
  _sfc_main as default
};
