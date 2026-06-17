import { useState, useEffect, useRef } from 'react';
import { Group, Rect, Text } from 'react-konva';

function getBackgroundProps(bgStyle, textBounds, stageDims) {
    const paddingX = stageDims.width * 0.03;
    const paddingY = stageDims.width * 0.02;
    const rectW = textBounds.width + paddingX * 2;
    const rectH = textBounds.height + paddingY * 2;

    const common = {
        x: -paddingX,
        y: -paddingY,
        width: rectW,
        height: rectH,
    };

    switch (bgStyle) {
        case 'pill':
            return {
                ...common,
                cornerRadius: rectH / 2,
                fill: '#FFFFFF',
                shadowColor: 'black',
                shadowBlur: 8,
                shadowOpacity: 0.15,
                shadowOffsetY: 2,
            };
        case 'box':
            return {
                ...common,
                cornerRadius: 8,
                fill: '#FFFFFF',
                shadowColor: 'black',
                shadowBlur: 8,
                shadowOpacity: 0.15,
                shadowOffsetY: 2,
            };
        case 'glass':
            return {
                ...common,
                cornerRadius: 12,
                fill: 'rgba(255, 255, 255, 0.25)',
                stroke: 'rgba(255, 255, 255, 0.4)',
                strokeWidth: 1,
            };
        default:
            return null;
    }
}

export default function DraggableText({
    text,
    stageDims,
    initialPositionRatio,
    fontReady,
    fontFamily = "Vogue, 'Playfair Display', serif",
    fontSizeDivisor = 18,
    fill = '#FFFFFF',
    shadowColor = 'black',
    shadowBlur = 6,
    shadowOpacity = 0.7,
    shadowOffsetY = 2,
    bgStyle = 'none',
    onPositionChange,
}) {
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [initialized, setInitialized] = useState(false);
    const [textBounds, setTextBounds] = useState({ width: 0, height: 0 });
    const textRef = useRef(null);

    // Set initial position once Stage has pixel dimensions
    useEffect(() => {
        if (stageDims.width > 0 && !initialized) {
            setPosition({
                x: stageDims.width * initialPositionRatio.x,
                y: stageDims.height * initialPositionRatio.y,
            });
            setInitialized(true);
        }
    }, [stageDims, initialized, initialPositionRatio]);

    // Measure text dimensions after render for Rect sizing and Group centering
    useEffect(() => {
        if (textRef.current) {
            setTextBounds({
                width: textRef.current.width(),
                height: textRef.current.height(),
            });
        }
    }, [text, stageDims, fontReady, fontFamily, fontSizeDivisor]);

    if (!stageDims.width || !fontReady) return null;

    const textFillMap = { pill: '#1A1611', box: '#1A1611', glass: '#FFFFFF', none: fill };
    const finalTextFill = textFillMap[bgStyle] ?? fill;
    const shouldShadowText = bgStyle === 'none' || bgStyle === 'glass';

    // Guard: only render Rect once text has been measured (avoids zero-size flash)
    const bgProps = textBounds.width > 0
        ? getBackgroundProps(bgStyle, textBounds, stageDims)
        : null;

    return (
        <Group
            x={position.x}
            y={position.y}
            offsetX={textBounds.width / 2}
            draggable={true}
            onDragEnd={(e) => {
                const newPos = { x: e.target.x(), y: e.target.y() };
                setPosition(newPos);
                if (onPositionChange) onPositionChange(newPos);
            }}
        >
            {bgProps && <Rect {...bgProps} />}
            <Text
                ref={textRef}
                text={text}
                x={0}
                y={0}
                fontSize={Math.round(stageDims.width / fontSizeDivisor)}
                fontFamily={fontFamily}
                fill={finalTextFill}
                shadowColor={shouldShadowText ? shadowColor : 'transparent'}
                shadowBlur={shouldShadowText ? shadowBlur : 0}
                shadowOpacity={shouldShadowText ? shadowOpacity : 0}
                shadowOffsetX={0}
                shadowOffsetY={shouldShadowText ? shadowOffsetY : 0}
            />
        </Group>
    );
}
