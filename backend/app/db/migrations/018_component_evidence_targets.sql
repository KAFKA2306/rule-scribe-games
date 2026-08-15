BEGIN;

-- #178: preserve first-class evidence semantics for component ingestion.
-- Do not coerce component-set / definition / component claims into game_metadata.

ALTER TABLE public.claims
  ADD COLUMN IF NOT EXISTS component_set_id text;

ALTER TABLE public.claims
  DROP CONSTRAINT IF EXISTS claims_target_type_check;
ALTER TABLE public.claims
  DROP CONSTRAINT IF EXISTS claims_check;
ALTER TABLE public.claims
  DROP CONSTRAINT IF EXISTS claims_component_target_fkey;
ALTER TABLE public.claims
  DROP CONSTRAINT IF EXISTS claims_component_set_target_fkey;
ALTER TABLE public.claims
  DROP CONSTRAINT IF EXISTS claims_property_definition_target_fkey;

ALTER TABLE public.claims
  ADD CONSTRAINT claims_target_type_check CHECK (
    target_type IN (
      'rule_node',
      'component',
      'component_set',
      'property_definition',
      'component_property',
      'ability_printed_text',
      'ability_normalized',
      'game_metadata'
    )
  ),
  ADD CONSTRAINT claims_component_target_fkey
    FOREIGN KEY (rule_set_id, component_id)
    REFERENCES public.components(rule_set_id, component_id)
    ON DELETE CASCADE,
  ADD CONSTRAINT claims_component_set_target_fkey
    FOREIGN KEY (rule_set_id, component_set_id)
    REFERENCES public.component_sets(rule_set_id, component_set_id)
    ON DELETE CASCADE,
  ADD CONSTRAINT claims_property_definition_target_fkey
    FOREIGN KEY (rule_set_id, property_key)
    REFERENCES public.component_property_definitions(rule_set_id, property_key)
    ON DELETE CASCADE,
  ADD CONSTRAINT claims_check CHECK (
    (
      target_type = 'rule_node' AND rule_id IS NOT NULL AND
      component_id IS NULL AND component_set_id IS NULL AND property_key IS NULL AND ordinal IS NULL AND
      ability_id IS NULL AND field_path IS NULL
    ) OR
    (
      target_type = 'component' AND rule_id IS NULL AND
      component_id IS NOT NULL AND component_set_id IS NULL AND property_key IS NULL AND ordinal IS NULL AND
      ability_id IS NULL AND field_path IS NULL
    ) OR
    (
      target_type = 'component_set' AND rule_id IS NULL AND
      component_id IS NULL AND component_set_id IS NOT NULL AND property_key IS NULL AND ordinal IS NULL AND
      ability_id IS NULL AND field_path IS NULL
    ) OR
    (
      target_type = 'property_definition' AND rule_id IS NULL AND
      component_id IS NULL AND component_set_id IS NULL AND property_key IS NOT NULL AND ordinal IS NULL AND
      ability_id IS NULL AND field_path IS NULL
    ) OR
    (
      target_type = 'component_property' AND rule_id IS NULL AND
      component_id IS NOT NULL AND component_set_id IS NULL AND property_key IS NOT NULL AND ordinal IS NOT NULL AND
      ability_id IS NULL AND field_path IS NULL
    ) OR
    (
      target_type IN ('ability_printed_text','ability_normalized') AND rule_id IS NULL AND
      component_id IS NULL AND component_set_id IS NULL AND property_key IS NULL AND ordinal IS NULL AND
      ability_id IS NOT NULL AND field_path IS NULL
    ) OR
    (
      target_type = 'game_metadata' AND rule_id IS NULL AND
      component_id IS NULL AND component_set_id IS NULL AND property_key IS NULL AND ordinal IS NULL AND
      ability_id IS NULL AND COALESCE(btrim(field_path), '') <> ''
    )
  );

CREATE INDEX IF NOT EXISTS claims_component_idx
  ON public.claims (rule_set_id, component_id)
  WHERE target_type = 'component';
CREATE INDEX IF NOT EXISTS claims_component_set_idx
  ON public.claims (rule_set_id, component_set_id)
  WHERE target_type = 'component_set';
CREATE INDEX IF NOT EXISTS claims_property_definition_idx
  ON public.claims (rule_set_id, property_key)
  WHERE target_type = 'property_definition';

COMMIT;
